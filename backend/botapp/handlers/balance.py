from aiogram import Router, F
from aiogram.types import Message
from users.models import User
from finance.models import Operation
from botapp.keyboards import main_kb
from asgiref.sync import sync_to_async

router = Router()

@router.message(F.text == "💰 Баланс")
async def show_balance(m: Message):
    user = await sync_to_async(
        lambda: User.objects.filter(tg_id=m.from_user.id).first()
    )()
    if not user:
        await m.answer("Сначала /start")
        return
    ops = await sync_to_async(
        lambda: list(
            Operation.objects
            .filter(user=user)
            .order_by("-created_at")
        )[:10]
    )()
    
    lines = [f"Баланс: {user.balance} STANOK"]
    if ops:
        lines.append("\nПоследние операции:")
        for op in ops:
            ts = op.created_at.strftime("%d.%m.%Y %H:%M")
            sign = "+" if op.amount >= 0 else ""
            if op.amount != 0.0:
                lines.append(f"{ts} {op.title} {sign}{op.amount}")
            # elif op.title == "Заявка на вывод":
            #     lines.append(f"{ts} #{op.id} — {op.title} — {sign}{op.amount}")
            else:
                lines.append(f"{ts} {op.title}")
    await m.answer("\n".join(lines), reply_markup=main_kb())
