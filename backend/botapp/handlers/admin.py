import aiohttp
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from decimal import Decimal
from django.conf import settings
from users.models import User
from finance.models import Operation, OperationType, WithdrawalRequest
from botapp.utils import get_user_by_username, adjust_balance, give_autoclaim
from asgiref.sync import sync_to_async
from finance.models import Settings
from autoclaim.models import AutoclaimSubscription
from datetime import timezone

router = Router()

def _price_key(plan_code: str) -> str:
    return {
        "1w": "AUTOCLAIM_PRICE_1W",
        "1m": "AUTOCLAIM_PRICE_1M",
        "6m": "AUTOCLAIM_PRICE_6M",
    }[plan_code]

def admin_only(message: Message) -> bool:
    return message.from_user and message.from_user.id == settings.ADMIN_TG_ID

router.message.filter(admin_only)

@router.message(Command("start"))
async def start(m: Message):
    await m.answer("Приветствую в админке STANOK Miner")

@router.message(Command("a_add"))
async def a_add(m: Message):
    try:
        _, uname, amount = m.text.split(maxsplit=2)
        amount = Decimal(amount)
    except Exception:
        await m.answer("Использование: /a_add @username amount")
        return
    user = await get_user_by_username(uname)
    if not user:
        await m.answer("Пользователь не найден")
        return
    await adjust_balance(user.pk, amount, "Пополнение STANOK", OperationType.DEPOSIT)
    # 3% реферальный бонус
    if user.ref_parent_id:
        bonus = (amount * Decimal('0.03')).quantize(Decimal('0.01'))
        print(user.ref_parent_id)
        await adjust_balance(user.ref_parent_id, bonus, f"Реферальный бонус за @{user.username}", OperationType.REFERRAL_BONUS)
    await m.answer(f"Зачислено {amount} STANOK пользователю @{user.username}")
    text = f"Зачислено {amount} STANOK"
    async with aiohttp.ClientSession() as session:
        await session.post(
            f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage",
            data={"chat_id": user.tg_id, "text": text}
        )

@router.message(Command("add_autoclaim"))
async def add_autoclaim(m: Message):
    try:
        _, uname, plan = m.text.split(maxsplit=2)
    except Exception:
        await m.answer("Использование: /add_autoclaim @username план автоклейма(1w|1m|6m)")
        return
    user = await get_user_by_username(uname)
    if not user:
        await m.answer("Пользовель не найден")
        return
    try:
        await give_autoclaim(user.pk, plan)
    except Exception as e:
        await m.answer(f"Возникла ошибка: {e}")
        print(e)
        return
    if plan[-3:] == "1w":
        autoclaim_type = "1 неделя"
    elif plan[-3:] == "1m":
        autoclaim_type = "1 месяц"
    else:
        autoclaim_type = "6 месяцев"
    print(plan[-3:])
    text = f"✅ Автоклей активирован\nСрок: {autoclaim_type}"
    async with aiohttp.ClientSession() as session:
        await session.post(
            f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage",
            data={"chat_id": user.tg_id, "text": text}
        )
    await m.answer(text = f"✅ Автоклей активирован\nСрок: {autoclaim_type}")


@router.message(Command("set_price"))
async def a_set_price(m: Message):
    try:
        _, plan, price = m.text.split(maxsplit=2)
        assert plan in ("1w", "1m", "6m")
        Decimal(price)  # валидация
    except Exception:
        await m.answer("Использование: /set_price 1w|1m|6m <цена в TON>")
        return
    key = _price_key(plan)
    obj, _ = await sync_to_async(Settings.objects.get_or_create)(key=key, defaults={"value": price})
    if obj.value != price:
        obj.value = price
        await sync_to_async(obj.save)(update_fields=["value"])
    await m.answer(f"Цена автоклейма {plan} установлена: {price} TON")
    

# @router.message(Command("a_adjust"))
# async def a_adjust(m: Message):
#     if not is_admin(m):
#         return
#     # /a_adjust @username amount title...
#     try:
#         parts = m.text.split(maxsplit=3)
#         _, uname, amount, title = parts[0], parts[1], parts[2], parts[3]
#         amount = Decimal(amount)
#     except Exception:
#         await m.answer("Использование: /a_adjust @username amount title")
#         return
#     user = get_user_by_username(uname)
#     if not user:
#         await m.answer("Пользователь не найден")
#         return
#     adjust_balance(user, amount, title, OperationType.ADJUSTMENT)
#     await m.answer(f"Корректировка {amount} STANOK для @{user.username}: {title}")

@router.message(Command("withdraws"))
async def a_withdraws(m: Message):
    reqs = await sync_to_async(
        lambda: list(
            WithdrawalRequest.objects
            .filter(status="PENDING")
            .order_by("created_at")
            .values("id", "amount_requested", "amount_after_tax", "created_at", "user__username")[:20]
        )
    )()
    print(reqs)
    if not reqs:
        await m.answer("Нет открытых заявок на вывод.")
        return
    lines = []
    for r in reqs:
        lines.append(f"#{r['id']} @{r['user__username']} запросил {r['amount_requested']} → к выдаче {r['amount_after_tax']}")
    await m.answer("\n".join(lines))

@router.message(Command("withdraw_done"))
async def a_withdraw_done(m: Message):
    try:
        _, rid = m.text.split(maxsplit=1)
        rid = int(rid)
    except Exception:
        await m.answer("Использование: /withdraw_done <id>")
        return
    from decimal import Decimal
    req = await sync_to_async(WithdrawalRequest.objects.select_related("user").filter(id=rid, status='PENDING').first)()
    if not req:
        await m.answer("Заявка не найдена или уже закрыта.")
        return
    user = req.user
    # списываем HOLD (уменьшаем hold), и фиксируем WITHDRAW_DONE (дурация баланса уже была списана при HOLD)
    user.balance_on_hold = (user.balance_on_hold - req.amount_requested).quantize(Decimal('0.01'))
    if user.balance_on_hold < 0:
        user.balance_on_hold = Decimal('0.00')
    await sync_to_async(user.save)(update_fields=['balance_on_hold'])
    await sync_to_async(Operation.objects.create)(user=user, type=OperationType.WITHDRAW_DONE, title=f"Вывод подтверждён #{req.id}", amount=Decimal('0.00'))
    req.status = 'DONE'
    await sync_to_async(req.save)(update_fields=['status'])
    await m.answer(f"Заявка #{req.id} завершена.")

@router.message(Command("user"))
async def a_user(m: Message):
    try:
        _, uname = m.text.split(maxsplit=1)
    except Exception:
        await m.answer("Использование: /user @username")
        return
    user = await get_user_by_username(uname)
    if not user:
        await m.answer("Пользователь не найден")
        return
    print(user.ref_parent_id)
    try:
        parent = await sync_to_async(User.objects.get)(pk=user.ref_parent_id)
    except Exception as e:
        None
    sub = await sync_to_async(AutoclaimSubscription.objects.filter(user=user).first)()
    if not sub:
        autoclaim_string = 'Автоклейм отсутствует'
    else:
        autoclaim_string = f'Автоклейм действует до {sub.active_until.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")}'
    lines = [
        f"@{user.username} (tg_id={user.tg_id})",
        f"Адрес: {user.ton_address}",
        f"Баланс: {user.balance} | HOLD: {user.balance_on_hold}",
        f"Реферер: @{parent.username}" if user.ref_parent_id else "Реферер: —",
    ]
    lines.append(autoclaim_string)
    await m.answer("\n".join(lines))
