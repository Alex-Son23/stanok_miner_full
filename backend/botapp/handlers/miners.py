from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from users.models import User
from miners.models import Miner, MinerLevel
from finance.models import Operation, OperationType
from botapp.keyboards import main_kb, claim_kb
from asgiref.sync import sync_to_async
from datetime import datetime
from finance.models import Operation, OperationType
from botapp.utils import make_miners_list


router = Router()

@router.message(F.text == "🛒 Купить майнер")
async def buy_prompt(m: Message):
    await m.answer("Введите сумму в STANOK, на которую купить майнер (например, 350000):")

@router.message(F.text.regexp(r"^\d+(\.\d{1,2})?$"))
async def buy_process(m: Message):
    user = await sync_to_async(
        lambda: User.objects.filter(tg_id=m.from_user.id).first()
    )()
    if not user:
        await m.answer("Сначала /start")
        return
    amount = Decimal(m.text)
    if amount <= 0:
        await m.answer("Сумма должна быть больше нуля.")
        return
    if user.balance < amount:
        await m.answer(f"Недостаточно средств. Ваш баланс: {user.balance} STANOK")
        return
    # Определяем уровень
    level = await sync_to_async(
        lambda: list(
            MinerLevel.objects
            .filter(active=True, min_amount__lte=amount)
            .order_by("min_amount")
        )
    )()
    selected = None
    for lvl in level:
        if lvl.max_amount is None or amount <= lvl.max_amount:
            selected = lvl
            break
    if not selected:
        await m.answer("Не удалось определить уровень для указанной суммы.")
        return
    # Списываем баланс и создаём майнер
    user.balance = (user.balance - amount).quantize(Decimal('0.01'))
    await sync_to_async(user.save)(update_fields=['balance'])
    await sync_to_async(Operation.objects.create)(user=user, type=OperationType.BUY_MINER, title=f"{selected.name}", amount=-amount)

    now = timezone.now()
    miner = await sync_to_async(Miner.objects.create)(
        user=user,
        level=selected,
        principal=amount,
        daily_percent=selected.daily_percent,
        created_at=now,
        expires_at=now + timedelta(days=365),
        next_claim_at=now + timedelta(hours=24),
        active=True
    )
    await m.answer(f"Куплен майнер {selected.name} на {amount} STANOK. Доход {selected.daily_percent}%/день. Первый клейм через 24ч.", reply_markup=main_kb())

@router.message(F.text == "⚙️ Мои майнеры")
async def my_miners(m: Message):
    user = await sync_to_async(User.objects.filter(tg_id=m.from_user.id).first, thread_sensitive=True)()
    if not user:
        await m.answer("Сначала /start")
        return
    miners = await sync_to_async(
        lambda: list(
            Miner.objects
            .filter(user_id=user.id)
            .select_related("level")
            .order_by("-created_at")
        )
    )()
    print(miners)
    if not miners:
        await m.answer("У вас нет майнеров.")
        return
    
    lines, miners_to_claim = make_miners_list(miners_list=miners)
    # for mn in miners:
    #     status = "активен" if (mn.active and now < mn.expires_at) else "истёк"
    #     left_days = max(0, (mn.expires_at - now).days)
    #     claim = "доступен" if mn.is_claim_available() else f"{int((mn.next_claim_at - now).total_seconds() // 3600)}"
    #     miner_name = " ".join(str(mn.level).split()[:3])
    #     # lines.append(f"• #{mn.id} {mn.level.name}: {mn.principal} STANOK, {status}, дней осталось: {left_days}, claim: {claim}")
    #     s = f"💠━━━━━━━━━━━━━━━💠\n💎{miner_name}💎\n🔋Статус: {status}\n🪙STANKO'в в работе: {mn.principal}\n📅Дней осталось: —  {left_days}\n⏳До клайма: {claim} часа\n💠━━━━━━━━━━━━━━━💠"
    #     lines.append(s)
    #     if claim == "доступен":
    #         miners_to_claim.append(mn)
    await m.answer("\n".join(lines), reply_markup=claim_kb(miners_to_claim=miners_to_claim))


from aiogram.types import Message
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

@router.message(F.text == "🏭 Управление майнингом")
async def mining_manage(m: Message):
    await m.answer("Здесь можно клеймить доступный доход по конкретным майнерам. Отправьте: claim <ID_майнера> (ID смотрите в 'Мои майнеры')")

@router.callback_query(F.data.startswith("claim"))
async def claim_by_id(call: CallbackQuery):
    user = await sync_to_async(User.objects.filter(tg_id=call.from_user.id).first, thread_sensitive=True)()
    if not user:
        await call.answer("Сначала /start")
        return
    miner_id = int(call.data.split()[-1])
    mn = await sync_to_async(Miner.objects.select_related('level').filter(id=miner_id, user=user).first, thread_sensitive=True)()
    if not mn:
        await call.answer("Майнер не найден.")
        return
    now = timezone.now()
    if not (mn.active and now >= mn.next_claim_at and now < mn.expires_at):
        await call.answer("Клейм недоступен сейчас.")
        return
    reward = mn.claim_amount()
    # начисляем
    await sync_to_async(Operation.objects.create)(user=user, type=OperationType.CLAIM, title=f"Claim по {mn.level.name} #{mn.id}", amount=reward)
    user.balance = (user.balance + reward).quantize(Decimal('0.01'))
    await sync_to_async(user.save)(update_fields=['balance'])

    # двигаем окно
    mn.next_claim_at = mn.next_claim_at + timedelta(hours=24)
    if now >= mn.expires_at:
        mn.active = False
    await sync_to_async(mn.save)(update_fields=['next_claim_at','active'])
    await call.answer(f"Начислено {reward} STANOK. Следующий claim после {mn.next_claim_at.strftime('%d.%m %H:%M UTC')}")

    miners = await sync_to_async(
        lambda: list(
            Miner.objects
            .filter(user_id=user.id)
            .select_related("level")
            .order_by("-created_at")
        )
    )()
    lines, miners_to_claim = make_miners_list(miners_list=miners)
    await call.message.edit_text("\n".join(lines), reply_markup=claim_kb(miners_to_claim=miners_to_claim))
