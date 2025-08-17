from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id','tg_id','username','ton_address','balance','balance_on_hold','ref_parent_id','registered_at')
    search_fields = ('username','ton_address','tg_id')
