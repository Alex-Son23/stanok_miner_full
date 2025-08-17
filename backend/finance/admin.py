from django.contrib import admin
from .models import Operation, WithdrawalRequest, Settings

admin.site.register(Operation)
admin.site.register(WithdrawalRequest)
admin.site.register(Settings)
