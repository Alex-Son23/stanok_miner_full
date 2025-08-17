import os
import asyncio
from django.core.management.base import BaseCommand
from django.conf import settings
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeDefault
from botapp.handlers import setup_admin_routers

class Command(BaseCommand):
    help = "Run aiogram3 admin-bot (long polling)"

    def handle(self, *args, **options):
        if not settings.BOT_ADMIN_TOKEN:
            self.stderr.write("BOT_TOKEN is empty")
            return
        asyncio.run(self._run())

    async def _run(self):
        bot = Bot(token=settings.BOT_ADMIN_TOKEN)
        await bot.set_my_commands(
            commands=[
                BotCommand(command="start", description="Запуск / регистрация"),
                BotCommand(command="a_add", description="Пополнить счет"),
                BotCommand(command="add_autoclaim", description="Выдать автоклейм"),
                BotCommand(command="set_price", description="Установить цену автоклейма"),
                BotCommand(command="withdraws", description="Выводы в обработке"),
                BotCommand(command="withdraw_done", description="Завершить этот вывод"),
                BotCommand(command="user", description="Статистика этого пользователя"),
            ],
            scope=BotCommandScopeDefault(),
            language_code="ru"
        )

        dp = Dispatcher()
        dp.include_router(setup_admin_routers())
        self.stdout.write("Bot polling started")
        await dp.start_polling(bot)
