from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from django.conf import settings
from users.models import User
from asgiref.sync import sync_to_async
from botapp.keyboards import deposit
import aiohttp


router = Router()

@router.message(F.text == "➕ Пополнить STANOK")
async def deposit_info(m: Message):
    user = await sync_to_async(User.objects.filter(tg_id=m.from_user.id).first, thread_sensitive=True)()
    if not user:
        await m.answer("Сначала /start")
        return
    addr = settings.DEPOSIT_STANOK_ADDRESS
    memo = f"@{user.username}"
    text = (
        "Пополнение STANOK\n\n"
        f"Адрес для пополнения (Jetton STANOK):\n`{addr}`\n\n"
        "ВАЖНО: В комментарии (memo) укажите **ваш Telegram @username**. Без memo средства не зачисляются.\n\n"
        "После перевода нажмите «Я оплатил», и админ подтвердит пополнение."
    )
    await m.answer(text, parse_mode="Markdown", reply_markup=deposit)
    # await m.answer("Я оплачал — напишите сюда сообщение с текстом: «Я оплатил» (оно уйдёт админу)")

@router.callback_query(F.data == "payed")
async def notify_paid(call: CallbackQuery):
    # bot = Bot(token=settings.BOT_ADMIN_TOKEN)
    text = f"💳 Пользователь @{call.from_user.username} сообщил о платеже."
    async with aiohttp.ClientSession() as session:
        await session.post(
            f"https://api.telegram.org/bot{settings.BOT_ADMIN_TOKEN}/sendMessage",
            data={"chat_id": settings.ADMIN_TG_ID, "text": text}
        )
    # await bot.send_message(chat_id=settings.ADMIN_TG_ID, text=text)
    await call.message.edit_text(text="Сообщение отправлено. Админ проверит и зачислит STANOK.")
