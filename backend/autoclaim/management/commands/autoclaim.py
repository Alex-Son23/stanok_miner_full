from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction, close_old_connections
from decimal import Decimal
from datetime import timedelta
import time
import signal
import os

from users.models import User
from miners.models import Miner
from finance.models import Operation, OperationType
from autoclaim.models import AutoclaimSubscription


class Command(BaseCommand):
    help = "Бесконечный цикл автоклейма. Делает проход по базе каждые N секунд (по умолчанию 300)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=int,
            default=int(os.environ.get("AUTOCLAIM_INTERVAL", "300")),  # 5 минут по умолчанию
            help="Пауза между проходами в секундах (по умолчанию 300).",
        )
        parser.add_argument(
            "--once",
            action="store_true",
            help="Сделать один проход и выйти (для отладки).",
        )

    def handle(self, *args, **opts):
        interval = max(5, int(opts["interval"]))  # минимум 5 сек, чтобы не спамить БД
        run_once = bool(opts["once"])

        # Грациозное завершение по SIGINT/SIGTERM
        stop = {"flag": False}
        def _graceful(*_):
            stop["flag"] = True
        signal.signal(signal.SIGINT, _graceful)
        signal.signal(signal.SIGTERM, _graceful)

        self.stdout.write(self.style.SUCCESS(
            f"autoclaim_loop запущен: интервал {interval}с. "
            f"{'(single pass)' if run_once else '(бесконечный цикл)'}"
        ))

        try:
            while True:
                t0 = time.monotonic()
                try:
                    close_old_connections()  # на всякий случай закрываем «устаревшие» коннекты
                    claimed = self._single_pass()
                    self.stdout.write(f"[{timezone.now():%Y-%m-%d %H:%M:%S}] Клеймов: {claimed}")
                except Exception as e:
                    # не падаем на одном исключении — лог и продолжили
                    self.stderr.write(self.style.WARNING(f"Ошибка в проходе автоклейма: {e!r}"))

                if run_once:
                    break
                # Выдерживаем интервал с учётом длительности прохода
                elapsed = time.monotonic() - t0
                sleep_for = max(1, interval - int(elapsed))
                for _ in range(sleep_for):
                    if stop["flag"]:
                        break
                    time.sleep(1)
                if stop["flag"]:
                    break

        finally:
            self.stdout.write(self.style.SUCCESS("autoclaim_loop завершён."))

    def _single_pass(self) -> int:
        """
        Один проход автоклейма.
        Логика:
          - Берём все активные подписки (active_until >= now).
          - Для каждого пользователя находим майнеры, у которых next_claim_at <= now и expires_at > now.
          - По КАЖДОМУ такому майнеру делаем максимум один клейм за проход (без догонялок):
              next_claim_at += 24h, reward = principal * daily_percent / 100 (округление до 0.01)
        Возвращаем количество успешных клеймов.
        """
        now = timezone.now()
        total_claims = 0

        subs = AutoclaimSubscription.objects.select_related("user").filter(active_until__gte=now)
        s = AutoclaimSubscription.objects.all()
        # Идём по подпискам стримом, чтобы не держать всё в памяти
        for sub in subs.iterator():
            user = sub.user
            # Майнеры, где клейм доступен сейчас
            miners_qs = Miner.objects.filter(
                user=user,
                active=True,
                next_claim_at__lte=now,
                expires_at__gt=now,
            ).order_by("next_claim_at")

            # По каждому доступному майнеру — один клейм
            for mn in miners_qs:
                reward = (mn.principal * mn.daily_percent / Decimal("100")).quantize(Decimal("0.01"))

                with transaction.atomic():
                    # Блокируем пользователя на время начисления
                    u = User.objects.select_for_update().get(pk=user.pk)
                    u.balance = (u.balance + reward).quantize(Decimal("0.01"))
                    u.save(update_fields=["balance"])

                    Operation.objects.create(
                        user=u,
                        type=OperationType.CLAIM,
                        title=f"Auto-claim по {mn.level.name} #{mn.id}",
                        amount=reward,
                    )

                    # Сдвигаем окно на +24 часа (строго, без «догонялок»)
                    mn.next_claim_at = mn.next_claim_at + timedelta(hours=24)
                    if now >= mn.expires_at:
                        mn.active = False
                    mn.save(update_fields=["next_claim_at", "active"])

                    total_claims += 1

        return total_claims
