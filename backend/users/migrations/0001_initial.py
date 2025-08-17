from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal

class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tg_id', models.BigIntegerField(unique=True)),
                ('username', models.CharField(max_length=32, unique=True)),
                ('ton_address', models.CharField(max_length=128, unique=True)),
                ('is_admin', models.BooleanField(default=False)),
                ('registered_at', models.DateTimeField(auto_now_add=True)),
                ('balance', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=18)),
                ('balance_on_hold', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=18)),
                ('ref_parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.user')),
            ],
        ),
    ]
