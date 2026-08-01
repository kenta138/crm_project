from django.contrib import admin

from labels.models import Label

from .models import Client, SystemSetting


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "phase", "assigned_user", "last_contact_date")
    list_filter = ("phase",)
    search_fields = ("name", "email")
    filter_horizontal = ("labels",)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # 管理画面上でも、無効化された項目(Label)は新規選択肢に出さない
        # (アプリ側のClientForm.labelsと同じ制約を管理画面にも適用する)。
        if db_field.name == "labels":
            kwargs["queryset"] = Label.objects.filter(is_active=True)
        return super().formfield_for_manytomany(db_field, request, **kwargs)


# SystemSettingはpk=1固定のシングルトン(models.py参照)なので、
# 管理画面から2件目を追加したり、唯一のレコードを削除したりできないようにする。
@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SystemSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
