from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Operation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('DEPOSIT', 'Пополнение'), ('BUY_MINER', 'Покупка майнера'), ('CLAIM', 'Клейм дохода'), ('WITHDRAW_HOLD', 'Заморозка на вывод'), ('WITHDRAW_DONE', 'Вывод выполнен'), ('REFERRAL_BONUS', 'Реферальный бонус'), ('ADJUSTMENT', 'Ручная корректировка')], max_length=32)),
                ('title', models.CharField(max_length=128)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=18)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('meta', models.JSONField(blank=True, default=dict)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
        ),
        migrations.CreateModel(
            name='Settings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=64, unique=True)),
                ('value', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='WithdrawalRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_requested', models.DecimalField(decimal_places=2, max_digits=18)),
                ('tax_percent', models.DecimalField(decimal_places=2, default=Decimal('2.00'), max_digits=5)),
                ('amount_after_tax', models.DecimalField(decimal_places=2, max_digits=18)),
                ('status', models.CharField(choices=[('PENDING', 'PENDING'), ('DONE', 'DONE'), ('CANCELLED', 'CANCELLED')], default='PENDING', max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
        ),
    ]
