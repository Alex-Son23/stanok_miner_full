from aiogram import Router, F
from aiogram.types import Message
from decimal import Decimal
from users.models import User
from finance.models import Operation, OperationType, WithdrawalRequest
from asgiref.sync import sync_to_async

router = Router()

MIN_WITHDRAW = Decimal('100000')
TAX = Decimal('0.02')  # 2%

@router.message(F.text == "📤 Вывести")
async def withdraw_prompt(m: Message):
    await m.answer(f"Введите команду вида: 'вывести <сумма>'. Минимум {MIN_WITHDRAW} STANOK. Налог 2%. Сумма сразу уходит в заморозку до подтверждения.")

@router.message(F.text.regexp(r"(?i)^вывести\s+\d+(?:\.\d{1,2})?$"))
async def withdraw_process(m: Message):
    user = await sync_to_async(User.objects.filter(tg_id=m.from_user.id).first, thread_sensitive=True)()
    if not user:
        await m.answer("Сначала /start")
        return
    try:
        amount_str = m.text.split()[1]
        amount = Decimal(amount_str)
    except Exception:
        await m.answer("Неверный формат. Пример: вывести 150000")
        return
    if amount < MIN_WITHDRAW:
        await m.answer(f"Минимальная сумма для вывода: {MIN_WITHDRAW}")
        return
    if user.balance < amount:
        await m.answer(f"Недостаточно средств. Баланс: {user.balance} STANOK")
        return
    amount_after_tax = (amount * (Decimal('1.00') - TAX)).quantize(Decimal('0.01'))
    # списываем в hold: уменьшаем баланс и увеличиваем hold
    user.balance -= amount
    user.balance_on_hold += amount
    user.balance = user.balance.quantize(Decimal('0.01'))
    user.balance_on_hold = user.balance_on_hold.quantize(Decimal('0.01'))
    user.save(update_fields=['balance','balance_on_hold'])
    await sync_to_async(Operation.objects.create)(user=user, type=OperationType.WITHDRAW_HOLD, title="Заявка на вывод", amount=-amount)
    req = await sync_to_async(WithdrawalRequest.objects.create)(
        user=user,
        amount_requested=amount,
        amount_after_tax=amount_after_tax,
        status='PENDING'
    )
    await m.answer(f"Заявка #{req.id} создана. К получению после налога: {amount_after_tax} STANOK. Вывод на основной адрес.")
