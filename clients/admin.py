from django.contrib import admin
from .models import Client, SystemSetting
from labels.models import Label
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'phase', 'assigned_user', 'last_contact_date')
    list_filter = ('phase',)
    search_fields = ('name', 'email')
    filter_horizontal = ('labels',)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'labels':
            kwargs['queryset'] = Label.objects.filter(is_active=True)
        return super().formfield_for_manytomany(db_field, request, **kwargs)
@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SystemSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False