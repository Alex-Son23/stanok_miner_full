from django.db import models
from django.utils import timezone
from users.models import User

class AutoclaimPlan(models.TextChoices):
    W1 = "1w", "1 неделя"
    M1 = "1m", "1 месяц"
    M6 = "6m", "6 месяцев"

class AutoclaimSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.CharField(max_length=8, choices=AutoclaimPlan.choices)
    active_until = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def is_active(self) -> bool:
        return timezone.now() < self.active_until

    def __str__(self):
        return f"{self.user.username}: {self.plan} до {self.active_until}"
