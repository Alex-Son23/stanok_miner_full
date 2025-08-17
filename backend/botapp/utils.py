from decimal import Decimal
from django.db import transaction
from users.models import User
from finance.models import Operation, OperationType
from django.utils import timezone
from asgiref.sync import sync_to_async
from django.utils import timezone

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
        claim = "доступен" if mn.is_claim_available() else f"{int((mn.next_claim_at - now).total_seconds() // 3600)}"
        miner_name = " ".join(str(mn.level).split()[:3])
        # lines.append(f"• #{mn.id} {mn.level.name}: {mn.principal} STANOK, {status}, дней осталось: {left_days}, claim: {claim}")
        s = f"💠━━━━━━━━━━━━━━━💠\n💎{miner_name} #{mn.id}💎\n🔋Статус: {status}\n🪙STANKO'в в работе: {mn.principal}\n📅Дней осталось: —  {left_days}\n"
        if claim == "доступен":
            miners_to_claim.append(mn)
            s += "✅Клейм доступен!\n💠━━━━━━━━━━━━━━━💠"
        else:
            s += f"⏳До клайма: {claim} часа\n💠━━━━━━━━━━━━━━━💠"
        lines.append(s)
    print(miners_to_claim)
    return lines, miners_to_claim
    
    
