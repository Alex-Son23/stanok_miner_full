from django.db import models
from decimal import Decimal
from users.models import User
from django.utils import timezone
from datetime import timedelta

class MinerLevel(models.Model):
    name = models.CharField(max_length=32)
    min_amount = models.DecimalField(max_digits=18, decimal_places=2)
    max_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)  # null -> без верхней границы
    daily_percent = models.DecimalField(max_digits=5, decimal_places=2)
    active = models.BooleanField(default=True)

    def __str__(self):
        up = f"-{self.max_amount}" if self.max_amount is not None else "+"
        return f"{self.name} {self.min_amount}{up} ({self.daily_percent}%)"

class Miner(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    level = models.ForeignKey(MinerLevel, on_delete=models.PROTECT)
    principal = models.DecimalField(max_digits=18, decimal_places=2)
    daily_percent = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    next_claim_at = models.DateTimeField()
    active = models.BooleanField(default=True)

    def is_claim_available(self):
        now = timezone.now()
        return self.active and (now >= self.next_claim_at) and (now < self.expires_at)

    def claim_amount(self):
        # round to 2 decimals
        return (self.principal * self.daily_percent / Decimal('100')).quantize(Decimal('0.01'))
