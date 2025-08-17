from django.db import models
from decimal import Decimal
from django.db.models import Q, UniqueConstraint


class User(models.Model):

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['ton_address'],
                condition=Q(ton_address__isnull=False) & ~Q(ton_address=''),
                name='uniq_nonempty_ton_address',
            )
        ]

    tg_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=32, unique=True)
    ton_address = models.CharField(max_length=128, null=True, blank=True)
    is_admin = models.BooleanField(default=False)

    ref_parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    registered_at = models.DateTimeField(auto_now_add=True)

    balance = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
    balance_on_hold = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"{self.username} ({self.tg_id})"
