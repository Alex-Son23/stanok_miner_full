from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from decimal import Decimal

import aiohttp
from django.conf import settings
from users.models import User
from finance.models import Operation, OperationType, WithdrawalRequest
from asgiref.sync import sync_to_async


router = Router()

class WithdrawState(StatesGroup):
    withdraw_value = State()

MIN_WITHDRAW = Decimal('100000')
TAX = Decimal('0.03')  # 2%

@router.message(F.text == "📤 Вывести")
async def withdraw_prompt(m: Message, state: FSMContext):
    await m.answer(f"Введите сумму вывода!")
    await state.set_state(WithdrawState.withdraw_value)

@router.message(WithdrawState.withdraw_value)
async def withdraw_process(m: Message, state: FSMContext):
    user = await sync_to_async(User.objects.filter(tg_id=m.from_user.id).first, thread_sensitive=True)()
    if not user:
        await m.answer("Сначала /start")
        return
    try:
        amount = Decimal(m.text)
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
    await sync_to_async(user.save)(update_fields=['balance','balance_on_hold'])
    await sync_to_async(Operation.objects.create)(user=user, type=OperationType.WITHDRAW_HOLD, title="Заявка на вывод", amount=-amount)
    req = await sync_to_async(WithdrawalRequest.objects.create)(
        user=user,
        amount_requested=amount,
        amount_after_tax=amount_after_tax,
        status='PENDING'
    )
    await state.clear()
    await m.answer(f"Заявка #{req.id} создана. К получению после налога: {amount_after_tax} STANOK. Вывод на основной адрес.")
    text = f"💳 Пользователь @{m.from_user.username} сделал запрос на вывод средства к оплате {amount_after_tax} STANOK."
    async with aiohttp.ClientSession() as session:
        await session.post(
            f"https://api.telegram.org/bot{settings.BOT_ADMIN_TOKEN}/sendMessage",
            data={"chat_id": settings.ADMIN_TG_ID, "text": text}
        )
