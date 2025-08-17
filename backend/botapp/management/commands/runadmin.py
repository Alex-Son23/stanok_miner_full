import os
import asyncio
from django.core.management.base import BaseCommand
from django.conf import settings
from aiogram import Bot, Dispatcher
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
        dp = Dispatcher()
        dp.include_router(setup_admin_routers())
        self.stdout.write("Bot polling started")
        await dp.start_polling(bot)
