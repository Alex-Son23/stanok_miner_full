import os
import asyncio
from django.core.management.base import BaseCommand
from django.conf import settings
from aiogram import Bot, Dispatcher
from botapp.handlers import setup_routers

class Command(BaseCommand):
    help = "Run aiogram3 bot (long polling)"

    def handle(self, *args, **options):
        if not settings.BOT_TOKEN:
            self.stderr.write("BOT_TOKEN is empty")
            return
        asyncio.run(self._run())

    async def _run(self):
        bot = Bot(token=settings.BOT_TOKEN)
        dp = Dispatcher()
        dp.include_router(setup_routers())
        self.stdout.write("Bot polling started")
        await dp.start_polling(bot)
