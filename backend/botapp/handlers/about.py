from aiogram import Router, F
from aiogram.types import Message
from django.conf import settings

router = Router()

@router.message(F.text == "ℹ️ О проекте")
async def about(m: Message):
    text = (
        "*О проекте STANOK*\n"
        f"CA Token: `{settings.CA_TOKEN}`\n"
        "Виртуальные STANOK ведутся во внутренней БД.\n"
        "Пополнение только Jetton STANOK на общий адрес с обязательным memo=@username.\n"
        "Вывод — только на основной TON-адрес, с которого были пополнения.\n"
    )
    await m.answer(text, parse_mode="Markdown")
