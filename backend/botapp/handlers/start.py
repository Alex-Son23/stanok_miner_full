from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from django.utils import timezone
from users.models import User
from botapp.keyboards import main_kb
from django.conf import settings
from asgiref.sync import sync_to_async
from aiogram.filters import CommandStart, CommandObject
from botapp.utils import is_valid_ton_wallet_common


router = Router()

class RegState(StatesGroup):
    waiting_ton = State()

@router.message(F.text == "/start")
async def start_cmd(m: Message, state: FSMContext):
    if not m.from_user.username:
        await m.answer("Для использования бота нужен установленный @username в Telegram. Пожалуйста задайте его в настройках и повторите /start.")
        return

    # parse ref from start param (t.me/...?start=<tg_id>)
    ref_parent = None
    if m.text and " " in m.text:
        try:
            ref_tg_id = int(m.text.split(" ", 1)[1].strip())
            if ref_tg_id != m.from_user.id:
                ref_parent = await sync_to_async(User.objects.filter(tg_id=ref_tg_id).first)()
        except Exception as e:
            print(f"ERROR {e}")
            pass

    user, created = await sync_to_async(User.objects.get_or_create)(
        tg_id=m.from_user.id,
        defaults={
            "username": m.from_user.username,
            "ton_address": "",
            "is_admin": (m.from_user.id == settings.ADMIN_TG_ID),
            "ref_parent": ref_parent
        }
    )
    if not created:
        # refresh username if changed
        if user.username != m.from_user.username:
            user.username = m.from_user.username
            await sync_to_async(user.save)(update_fields=["username"])

    if not user.ton_address:
        await m.answer("Добро пожаловать! Укажите ваш основной TON-адрес (куда будут выводы и откуда пополнения):")
        await state.set_state(RegState.waiting_ton)
        return
    await m.answer("Вы уже зарегистрированы. Главное меню:", reply_markup=main_kb())


@router.message(CommandStart(deep_link=True))
async def start_cmd(m: Message, command: CommandObject, state: FSMContext):
    if not m.from_user.username:
        await m.answer("Для использования бота нужен установленный @username в Telegram. Пожалуйста задайте его в настройках и повторите /start.")
        return

    # parse ref from start param (t.me/...?start=<tg_id>)
    ref_parent = None
    if m.text and " " in m.text:
        try:
            ref_tg_id = int(m.text.split(" ", 1)[1].strip())
            if ref_tg_id != m.from_user.id:
                ref_parent = await sync_to_async(User.objects.filter(tg_id=ref_tg_id).first)()
        except Exception as e:
            print(f"ERROR {e}")
            pass
    user, created = await sync_to_async(User.objects.get_or_create)(
        tg_id=m.from_user.id,
        defaults={
            "username": m.from_user.username,
            "ton_address": "",
            "is_admin": (m.from_user.id == settings.ADMIN_TG_ID),
            "ref_parent": ref_parent
        }
    )
    if not created:
        # refresh username if changed
        if user.username != m.from_user.username:
            user.username = m.from_user.username
            user.save(update_fields=["username"])

    if not user.ton_address:
        await m.answer("Добро пожаловать! Укажите ваш основной TON-адрес (куда будут выводы и откуда пополнения):")
        await state.set_state(RegState.waiting_ton)
        return
    await m.answer("Вы уже зарегистрированы. Главное меню:", reply_markup=main_kb())


@router.message(RegState.waiting_ton)
async def save_ton(m: Message, state: FSMContext):
    addr = m.text.strip()
    if not is_valid_ton_wallet_common(addr):
        await m.answer("Похоже на неверный TON-адрес. Отправьте корректный адрес.")
        return
    user = await sync_to_async(User.objects.get)(tg_id=m.from_user.id)
    user.ton_address = addr
    if m.from_user.id == settings.ADMIN_TG_ID:
        user.is_admin = True
    await sync_to_async(user.save)(update_fields=["ton_address", "is_admin"])
    await state.clear()
    await m.answer("Готово. Ваш адрес сохранён. Открываю меню.", reply_markup=main_kb())
