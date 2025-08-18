from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from django.conf import settings
from users.models import User
from asgiref.sync import sync_to_async
from botapp.keyboards import deposit, buy_autoclaim
import aiohttp
# from html import escape as h
from finance.models import Settings
from autoclaim.models import AutoclaimSubscription
from botapp.utils import days_hours_left


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
    user = await sync_to_async(User.objects.filter(username=call.from_user.username).first)()
    text = f"💳 Пользователь @{call.from_user.username} сообщил о ПЛАТЕЖЕ.\n<code>{user.ton_address}</code>"
    async with aiohttp.ClientSession() as session:
        await session.post(
            f"https://api.telegram.org/bot{settings.BOT_ADMIN_TOKEN}/sendMessage",
            data={"chat_id": settings.ADMIN_TG_ID, "text": text, "parse_mode": "html"}
        )
    # await bot.send_message(chat_id=settings.ADMIN_TG_ID, text=text)
    await call.message.edit_text(text="Сообщение отправлено. Админ проверит и зачислит STANOK.")

@router.callback_query(F.data == "cancel_payment")
async def notify_paid(call: CallbackQuery):
    await call.message.edit_text("Покупка отменена")


@router.message(F.text == "⏰ Купить автоклейм")
async def autoclaim_info(m: Message):
    user = await sync_to_async(User.objects.filter(tg_id=m.from_user.id).first, thread_sensitive=True)()
    if not user:
        await m.answer("Сначала /start")
        return
    sub = await sync_to_async(AutoclaimSubscription.objects.select_related('user').filter(user_id=user.id).first)()

    if sub:
        d, h, minutes = days_hours_left(sub.active_until)
        await m.answer(f"У вас уже есть автоклейм активный еще {d} дней {h} часов {minutes} минут")
        return
    addr = settings.DEPOSIT_STANOK_ADDRESS
    # "1w": "AUTOCLAIM_PRICE_1W",
    #     "1m": "AUTOCLAIM_PRICE_1M",
    #     "6m": "AUTOCLAIM_PRICE_6M",
    one_week = await sync_to_async(Settings.objects.filter(key="AUTOCLAIM_PRICE_1W").first)()
    one_month = await sync_to_async(Settings.objects.filter(key="AUTOCLAIM_PRICE_1M").first)()
    six_months = await sync_to_async(Settings.objects.filter(key="AUTOCLAIM_PRICE_6M").first)()
    text = (
        "<b>Покупка автоклейма</b>\n\n"
        "Адрес для пополнения (TON):\n"
        f"<code>{addr}</code>\n\n"
        "ВАЖНО: В комментарии (memo) укажите ваш Telegram @username и план автоклейма "
        "<code>autoclaim_1w</code>, <code>autoclaim_1m</code>, <code>autoclaim_6m</code>.\n\n"
        f"На 1 неделю({one_week.value} TON), 1 месяц({one_month.value} TON) и 6 месяцев({six_months.value} TON) соответственно."
        "Без memo средства не зачисляются. После перевода нажмите «Я оплатил», и админ подтвердит пополнение."
    )
    await m.answer(text, parse_mode="html", reply_markup=buy_autoclaim)
    # await m.answer("Я оплачал — напишите сюда сообщение с текстом: «Я оплатил» (оно уйдёт админу)")


@router.callback_query(F.data == "payed_autoclaim")
async def notify_paid(call: CallbackQuery):
    # bot = Bot(token=settings.BOT_ADMIN_TOKEN)
    user = await sync_to_async(User.objects.filter(username=call.from_user.username).first)()
    text = f"💳 Пользователь @{call.from_user.username} сообщил о покупке АВТОКЛЕЙМА.\n<code>{user.ton_address}</code>"
    async with aiohttp.ClientSession() as session:
        await session.post(
            f"https://api.telegram.org/bot{settings.BOT_ADMIN_TOKEN}/sendMessage",
            data={"chat_id": settings.ADMIN_TG_ID, "text": text, "parse_mode": "html"}
        )
    # await bot.send_message(chat_id=settings.ADMIN_TG_ID, text=text)
    await call.message.edit_text(text="Сообщение отправлено. Админ проверит и включит вам автоклейм.")
