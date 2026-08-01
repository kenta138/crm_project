from django.db import models

from accounts.models import User
from clients.models import Client


# 現状ContactLog.methodの選択肢(METHOD_CHOICES)は固定リストのため未使用だが、
# 将来的に接触方法をマスタデータとして自由に追加できるようにする場合の受け皿として定義されているモデル。
class ContactMethod(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "接触方法"
        verbose_name_plural = "接触方法"


class ContactLog(models.Model):
    # 接触方法の選択肢。ContactMethodモデルとは別に、フォームの選択肢として固定で持たせている。
    # 「来訪」(先方がこちらに来る)と「訪問」(こちらから先方に出向く)を区別して持つ。
    METHOD_CHOICES = [
        ("phone", "電話"),
        ("email", "メール"),
        ("line", "LINE"),
        ("visit", "来訪"),
        ("our_visit", "訪問"),
        ("online", "オンライン"),
        ("other", "その他"),
    ]

    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="contact_logs"
    )
    # 削除済みユーザーが担当していた記録も残すため、CASCADEではなくSET_NULLにしている。
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="contact_logs"
    )
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default="phone")
    date = models.DateTimeField()
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)  # 論理削除用

    def __str__(self):
        return f"{self.client.name} - {self.title}"

    class Meta:
        verbose_name = "接触記録"
        verbose_name_plural = "接触記録"
        ordering = ["-date"]  # 一覧のデフォルト表示順は接触日時の新しい順
