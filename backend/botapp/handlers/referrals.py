from aiogram import Router, F
from aiogram.types import Message
from users.models import User
from finance.models import Operation, OperationType
from asgiref.sync import sync_to_async

router = Router()

@router.message(F.text == "👥 Мои рефералы")
async def my_refs(m: Message):
    user = await sync_to_async(User.objects.filter(tg_id=m.from_user.id).first)()
    if not user:
        await m.answer("Сначала /start")
        return
    kids = await sync_to_async(lambda: list(User.objects.filter(ref_parent=user).order_by("-registered_at")))()
    referal_bonus_list = await sync_to_async(lambda: list(Operation.objects.filter(user=user, type=OperationType.REFERRAL_BONUS)))()
    income = sum(op.amount for op in referal_bonus_list)
    ref_link = f"https://t.me/marke_example_evacode_bot?start={user.tg_id}"
    lines = [
        f"Приглашённых: {len(kids)}",
        f"Заработано на рефералах: {income} STANOK",
        f"Ваша ссылка: {ref_link}",
    ]
    if user.ref_parent_id:
        parent = await sync_to_async(User.objects.get)(pk=user.ref_parent_id)
        lines.insert(0, f"Вас пригласил: {parent.username}")
    if kids:
        lines.append("\nСписок:")
        for k in kids[:20]:
            lines.append(f"• @{k.username} — {k.registered_at.strftime('%d.%m.%Y')}")
    await m.answer("\n".join(lines))
