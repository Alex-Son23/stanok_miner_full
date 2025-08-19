from decimal import Decimal
from django.db import transaction
from users.models import User
from finance.models import Operation, OperationType
from autoclaim.models import AutoclaimSubscription
from django.utils import timezone
from asgiref.sync import sync_to_async
from datetime import timedelta
from typing import Optional
from tonsdk.utils import Address


@sync_to_async
def adjust_balance(user: User | int, amount: Decimal, title: str, op_type: str) -> Operation:
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=user)
        user.balance = (user.balance + amount).quantize(Decimal('0.01'))
        user.save(update_fields=['balance'])
        op = Operation.objects.create(user=user, type=op_type, title=title, amount=amount)
        return op

@sync_to_async
def get_user_by_username(username: str) -> User | None:
    uname = username.lstrip('@')
    try:
        return User.objects.get(username=uname)
    except User.DoesNotExist:
        return None


def make_miners_list(miners_list) -> list:
    now = timezone.now()
    miners_to_claim = []
    lines = []
    for mn in miners_list:
        status = "активен" if (mn.active and now < mn.expires_at) else "истёк"
        left_days = max(0, (mn.expires_at - now).days)
        ld, lh, lm = days_hours_left(mn.expires_at)
        print("CHEEEECK")
        d, h, m = days_hours_left(mn.next_claim_at)
        claim = "доступен" if mn.is_claim_available() else "недоступен"
        miner_name = " ".join(str(mn.level).split()[:3])
        # lines.append(f"• #{mn.id} {mn.level.name}: {mn.principal} STANOK, {status}, дней осталось: {left_days}, claim: {claim}")
        s = f"💎{miner_name} #{mn.id}💎\n🔋Статус: {status}\n🪙STANKO'в в работе: {mn.principal}\n📅Работать осталось: {ld} дней {lh} часов {lm} минут\n"
        if claim == "доступен":
            miners_to_claim.append(mn)
            s += "✅Клейм доступен!\n💠━━━━━━━━━━━━━━━💠"
        else:
            if h == 0:
                s += f"⏳До клайма: {m} минут\n💠━━━━━━━━━━━━━━━💠"
            else:
                s += f"⏳До клайма: {h} часов {m} минут\n💠━━━━━━━━━━━━━━━💠"
        lines.append(s)
    print(miners_to_claim)
    return lines, miners_to_claim
    
@sync_to_async
def give_autoclaim(user_id: int, plan: str):
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=user_id)
        sub = AutoclaimSubscription.objects.filter(user=user).first()
        now = timezone.now()
        delta = {"1w": timedelta(days=7), "1m": timedelta(days=30), "6m": timedelta(days=180)}[plan[-2:]]
        if sub:
            # продлеваем от большего из (now, current)
            start_from = sub.active_until if sub.active_until > now else now
            sub.plan = plan
            sub.active_until = start_from + delta
            print(sub)
            sub.save(update_fields=["plan", "active_until"])
        else:
            AutoclaimSubscription.objects.create(user=user, plan=plan, active_until=now + delta)


def days_hours_left(end_dt):
    """
    Возвращает (days, hours) до end_dt.
    Если срок истёк — (0, 0).
    """
    now = timezone.now()
    delta = end_dt - now
    if delta.total_seconds() <= 0:
        return 0, 0, 0
    days = delta.days if delta.days else None
    hours = delta.seconds // 3600  # остаток часов внутри суток
    t = delta.seconds % 3600
    minutes = t // 60
    return days, hours, minutes


FORBIDDEN = set(" \t\r\n/\\?#&=")

def normalize_ton_wallet_common(addr: str) -> Optional[str]:
    """
    Принимает ТОЛЬКО обычный кошелёк в формате UQ… (friendly, url-safe, non-bounceable).
    Deeplink-и/сырые адреса/тестнет — отвергаем.
    Возвращает нормализованный UQ… (mainnet) или None.
    """
    if not addr:
        return None
    s = addr.strip()
    # ничего, что похоже на ссылку/лишние символы
    if "://" in s or any(ch in FORBIDDEN for ch in s):
        return None

    try:
        a = Address(s)              # tonsdk сам проверит CRC/длину/алфавит
        # только основной чейн кошельков (wc=0) и не тестовая сеть
        if getattr(a, "is_test_only", False) or getattr(a, "wc", 0) != 0:
            return None

        # нормализуем в user-friendly, url-safe, non-bounceable => UQ…
        friendly = a.to_string(
            is_user_friendly=True,
            is_url_safe=True,
            is_bounceable=False,    # именно non-bounceable (UQ…)
            is_test_only=False,
        )
        return friendly if friendly.startswith("UQ") else None
    except Exception:
        return None

def is_valid_ton_wallet_common(addr: str) -> bool:
    return normalize_ton_wallet_common(addr) is not None
