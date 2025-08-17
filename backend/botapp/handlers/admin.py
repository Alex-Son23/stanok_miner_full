import aiohttp
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from decimal import Decimal
from django.conf import settings
from users.models import User
from finance.models import Operation, OperationType, WithdrawalRequest
from botapp.utils import get_user_by_username, adjust_balance
from asgiref.sync import sync_to_async

router = Router()

# def is_admin(m: Message) -> bool:
#     return m.from_user and (m.from_user.id == settings.ADMIN_TG_ID)

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

@router.message(Command("a_adjust"))
async def a_adjust(m: Message):
    if not is_admin(m):
        return
    # /a_adjust @username amount title...
    try:
        parts = m.text.split(maxsplit=3)
        _, uname, amount, title = parts[0], parts[1], parts[2], parts[3]
        amount = Decimal(amount)
    except Exception:
        await m.answer("Использование: /a_adjust @username amount title")
        return
    user = get_user_by_username(uname)
    if not user:
        await m.answer("Пользователь не найден")
        return
    adjust_balance(user, amount, title, OperationType.ADJUSTMENT)
    await m.answer(f"Корректировка {amount} STANOK для @{user.username}: {title}")

@router.message(Command("a_withdraws"))
async def a_withdraws(m: Message):
    if not is_admin(m):
        return
    reqs = WithdrawalRequest.objects.filter(status='PENDING').order_by('created_at')[:20]
    if not reqs:
        await m.answer("Нет открытых заявок на вывод.")
        return
    lines = []
    for r in reqs:
        lines.append(f"#{r.id} @{r.user.username} запросил {r.amount_requested} → к выдаче {r.amount_after_tax}")
    await m.answer("\n".join(lines))

@router.message(Command("a_withdraw_done"))
async def a_withdraw_done(m: Message):
    if not is_admin(m):
        return
    try:
        _, rid = m.text.split(maxsplit=1)
        rid = int(rid)
    except Exception:
        await m.answer("Использование: /a_withdraw_done <id>")
        return
    from decimal import Decimal
    req = WithdrawalRequest.objects.filter(id=rid, status='PENDING').first()
    if not req:
        await m.answer("Заявка не найдена или уже закрыта.")
        return
    user = req.user
    # списываем HOLD (уменьшаем hold), и фиксируем WITHDRAW_DONE (дурация баланса уже была списана при HOLD)
    user.balance_on_hold = (user.balance_on_hold - req.amount_requested).quantize(Decimal('0.01'))
    if user.balance_on_hold < 0:
        user.balance_on_hold = Decimal('0.00')
    user.save(update_fields=['balance_on_hold'])
    Operation.objects.create(user=user, type=OperationType.WITHDRAW_DONE, title=f"Вывод подтверждён #{req.id}", amount=Decimal('0.00'))
    req.status = 'DONE'
    req.save(update_fields=['status'])
    await m.answer(f"Заявка #{req.id} завершена.")

@router.message(Command("a_user"))
async def a_user(m: Message):
    if not is_admin(m):
        return
    try:
        _, uname = m.text.split(maxsplit=1)
    except Exception:
        await m.answer("Использование: /a_user @username")
        return
    user = get_user_by_username(uname)
    if not user:
        await m.answer("Пользователь не найден")
        return
    lines = [
        f"@{user.username} (tg_id={user.tg_id})",
        f"Адрес: {user.ton_address}",
        f"Баланс: {user.balance} | HOLD: {user.balance_on_hold}",
        f"Реферер: @{user.ref_parent.username}" if user.ref_parent else "Реферер: —",
    ]
    await m.answer("\n".join(lines))
