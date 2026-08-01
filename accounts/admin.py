from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


# emailログイン・roleフィールドを持つカスタムUserモデル用に、
# Django標準のUserAdminのフィールド構成(username前提)を上書きしている。
# サインアップ直後のユーザーはis_active=Falseのため、ここでis_activeをTrueにするのが
# 管理者による承認操作にあたる(accounts/views.py.signup参照)。
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "name", "role", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("email", "name")
    ordering = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("基本情報", {"fields": ("name", "role")}),
        ("権限", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "name", "role", "password1", "password2"),
            },
        ),
    )
