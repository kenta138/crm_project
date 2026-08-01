from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


# USERNAME_FIELDをemailにするため、username不要のカスタムマネージャーが必要
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("メールアドレスは必須です")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        # createsuperuserコマンド実行時に、管理者権限一式を自動付与する
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        return self.create_user(email, password, **extra_fields)


# emailログイン・ロールベース権限(admin/manager/member)を持つカスタムユーザーモデル。
# settings.AUTH_USER_MODELでDjango標準のUserと差し替えて使用する。
class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("admin", "Admin"),  # 全操作可能(取引先削除・ラベル管理など)
        ("manager", "Manager"),  # 取引先・接触記録・タスクの編集が可能
        ("member", "Member"),  # 閲覧と自分が担当するデータの操作が中心
    ]
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")
    is_active = models.BooleanField(
        default=True
    )  # 管理者による承認待ち/無効化の判定に使用
    is_staff = models.BooleanField(default=False)  # Django管理画面へのログイン可否
    deleted_at = models.DateTimeField(
        null=True, blank=True
    )  # 論理削除用(物理削除はしない)

    USERNAME_FIELD = "email"  # ログインIDとしてusernameではなくemailを使う
    REQUIRED_FIELDS = ["name"]

    objects = UserManager()

    def __str__(self):
        return self.name
