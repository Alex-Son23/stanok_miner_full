from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Купить майнер"), KeyboardButton(text="⚙️ Мои майнеры")],
            [KeyboardButton(text="⏰ Купить автоклейм"), KeyboardButton(text="💰 Баланс")],
            [KeyboardButton(text="➕ Пополнить STANOK"), KeyboardButton(text="📤 Вывести")],
            [KeyboardButton(text="👥 Мои рефералы"), KeyboardButton(text="ℹ️ О проекте")],
        ],
        resize_keyboard=True
    )


deposit = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Я оплатил✅", callback_data="payed")],
    [InlineKeyboardButton(text="Отмена❌", callback_data="cancel_payment")]
])


buy_autoclaim = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Я оплатил✅", callback_data="payed_autoclaim")],
    [InlineKeyboardButton(text="Отмена❌", callback_data="cancel_payment")]
])


def claim_kb(miners_to_claim: list) -> InlineKeyboardMarkup:
    mn_button_list = []
    button_layer = []
    for mn in miners_to_claim:
        button_layer.append(InlineKeyboardButton(text=f"Claim #{mn.id}", callback_data=f"claim {mn.id}"))
        if len(button_layer) == 2:
            mn_button_list.append(button_layer)
            button_layer = []
    if button_layer:
        mn_button_list.append(button_layer)
    return InlineKeyboardMarkup(inline_keyboard=mn_button_list)
