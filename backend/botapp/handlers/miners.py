from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
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
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from autoclaim.models import AutoclaimSubscription
from botapp.utils import days_hours_left
from django.conf import settings
from django.contrib.staticfiles import finders


router = Router()

def _find_static(path: str) -> str | None:
    """
    Ищем файл в статике (и в app static, и в STATICFILES_DIRS).
    Примеры путей:
      - "botapp/promo.jpg"        (если лежит в botapp/static/botapp/promo.jpg)
      - "images/promo.jpg"        (если лежит в static/images/promo.jpg)
    """
    return finders.find(path)

class DepositState(StatesGroup):
    deposit = State()


@router.message(F.text == "🛒 Купить майнер")
async def buy_prompt(m: Message, state: FSMContext):
    path = _find_static("images/prices.jpeg")
    print(path)
    photo = FSInputFile(path)
    await m.answer_photo(photo, caption="Введите сумму в STANOK, на которую купить майнер (например, 350000)")
    # await m.answer(
    # "<code>Уровень     Цена      Доход/день.   Срок</code>\n"
    # "<code>-------------------------------------------------------</code>\n"
    # "<code>MicroMiner  100k-499k # 0.5% в День (365 дней)</code>\n"
    # "<code>MiniMiner   500k-999k # 0.6% в День (365 дней)</code>\n"
    # "<code>NormalMiner 500k-999k # 0.6% в День (365 дней)</code>\n"
    # "<code>NormalMinerLvl3 | 1,000,000–2,999,999| 0.7%      | 365 дней</code>\n"
    # "<code>BigMiner   Lvl4 | 3,000,000–4,999,999| 0.8%      | 365 дней</code>\n"
    # "<code>UltraMiner Lvl5 | 5,000,000+         | 1.0%      | 365 дней:</code>\n"
    # "Введите сумму в STANOK, на которую купить майнер (например, 350000)", parse_mode="html"
    # )
    await state.set_state(DepositState.deposit)

@router.message(DepositState.deposit)
async def buy_process(m: Message, state: FSMContext):
    user = await sync_to_async(
        lambda: User.objects.filter(tg_id=m.from_user.id).first()
    )()
    if not user:
        await m.answer("Сначала /start")
        return
    try:
        amount = Decimal(m.text)
    except Exception as e:
        await m.answer("Для покупки майнера нужно ввести сумму без букв и других символов.\nПопробуйте приобрести майнер еще раз")
        await state.clear()
        return
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
    await state.clear()

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
    # autoclaim = await sync_to_async(AutoclaimSubscription.objects.select_related("user").filter(user=user).first)()
    autoclaim = await sync_to_async(
        lambda: AutoclaimSubscription.objects
            .select_related('user')                 # <-- важно
            .filter(user_id=user.id)
            .first()
    )()
    t = f"Автоклейм не активен!\n"
    if autoclaim:
        print(autoclaim)
        d, h, _ = days_hours_left(autoclaim.active_until)
        if d != 0 or h != 0:
            t = f"Автоклейм активен!\nДо окончания действия автоклейма осталось: {d} дней {h} часов"
    lines, miners_to_claim = make_miners_list(miners_list=miners)
    lines.insert(0, t)
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
