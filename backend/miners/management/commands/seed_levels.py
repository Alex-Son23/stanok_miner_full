from django.core.management.base import BaseCommand
from decimal import Decimal
from miners.models import MinerLevel

class Command(BaseCommand):
    help = "Seed miner levels from the spec"

    def handle(self, *args, **options):
        data = [
            ("MicroMiner (Lvl 1)", Decimal('100000'), Decimal('499999'), Decimal('0.50')),
            ("MiniMiner (Lvl 2)", Decimal('500000'), Decimal('999999'), Decimal('0.60')),
            ("NormalMiner (Lvl 3)", Decimal('1000000'), Decimal('2999999'), Decimal('0.70')),
            ("BigMiner (Lvl 4)", Decimal('3000000'), Decimal('4999999'), Decimal('0.80')),
            ("UltraMiner (Lvl 5)", Decimal('5000000'), None, Decimal('1.00')),
        ]
        created = 0
        for name, mn, mx, pct in data:
            obj, was_created = MinerLevel.objects.get_or_create(
                name=name,
                defaults=dict(min_amount=mn, max_amount=mx, daily_percent=pct, active=True)
            )
            if not was_created:
                obj.min_amount = mn
                obj.max_amount = mx
                obj.daily_percent = pct
                obj.active = True
                obj.save()
            created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded/updated {created} levels"))
