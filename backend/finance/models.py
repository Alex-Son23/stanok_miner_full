from django.db import models
from decimal import Decimal
from users.models import User

class OperationType(models.TextChoices):
    DEPOSIT = 'DEPOSIT', 'Пополнение'
    BUY_MINER = 'BUY_MINER', 'Покупка майнера'
    CLAIM = 'CLAIM', 'Клейм дохода'
    WITHDRAW_HOLD = 'WITHDRAW_HOLD', 'Заморозка на вывод'
    WITHDRAW_DONE = 'WITHDRAW_DONE', 'Вывод выполнен'
    REFERRAL_BONUS = 'REFERRAL_BONUS', 'Реферальный бонус'
    ADJUSTMENT = 'ADJUSTMENT', 'Ручная корректировка'

class Operation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=32, choices=OperationType.choices)
    title = models.CharField(max_length=128)
    amount = models.DecimalField(max_digits=18, decimal_places=2)  # + или -
    created_at = models.DateTimeField(auto_now_add=True)
    meta = models.JSONField(default=dict, blank=True)

    def __str__(self):
        sign = '+' if self.amount >= 0 else ''
        return f"{self.user.username} {self.type} {sign}{self.amount} ({self.title})"

class WithdrawalRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount_requested = models.DecimalField(max_digits=18, decimal_places=2)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('2.00'))
    amount_after_tax = models.DecimalField(max_digits=18, decimal_places=2)
    status = models.CharField(max_length=16, choices=[('PENDING','PENDING'),('DONE','DONE'),('CANCELLED','CANCELLED')], default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Withdraw {self.id} {self.user.username} {self.amount_after_tax} {self.status}"

class Settings(models.Model):
    key = models.CharField(max_length=64, unique=True)
    value = models.CharField(max_length=256)

    def __str__(self):
        return f"{self.key}={self.value}"
