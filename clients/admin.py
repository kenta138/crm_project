from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'phase', 'assigned_user', 'last_contact_date')
    list_filter = ('phase',)
    search_fields = ('name', 'email')
    filter_horizontal = ('labels',)