from django.core.management.base import BaseCommand
from decimal import Decimal
from finance.models import Settings

class Command(BaseCommand):
    help = "Создает базовые прайсы автоклеймам по их плану"

    def handle(self, *args, **options):
        data = [
            ("AUTOCLAIM_PRICE_1W", Decimal('1')),
            ("AUTOCLAIM_PRICE_1M", Decimal('2')),
            ("AUTOCLAIM_PRICE_6M", Decimal('3')),
        ]
        created = 0
        for plan, price in data:
            obj, was_created = Settings.objects.get_or_create(
                key=plan,
                value=price
            )
            if not was_created:
                obj.key = plan
                obj.value = price
                obj.save()
            created += 1
        self.stdout.write(self.style.SUCCESS(f"Добавлены/созданы прайсы на автоклйем {created} уровней"))
