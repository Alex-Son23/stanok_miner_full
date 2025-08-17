from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MinerLevel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32)),
                ('min_amount', models.DecimalField(decimal_places=2, max_digits=18)),
                ('max_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=18, null=True)),
                ('daily_percent', models.DecimalField(decimal_places=2, max_digits=5)),
                ('active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Miner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('principal', models.DecimalField(decimal_places=2, max_digits=18)),
                ('daily_percent', models.DecimalField(decimal_places=2, max_digits=5)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('next_claim_at', models.DateTimeField()),
                ('active', models.BooleanField(default=True)),
                ('level', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='miners.minerlevel')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
        ),
    ]
