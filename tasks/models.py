from django.db import models

from accounts.models import User
from clients.models import Client
from contacts.models import ContactLog


class Task(models.Model):
    STATUS_CHOICES = [
        ("pending", "未着手"),
        ("in_progress", "対応中"),
        ("done", "完了"),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="tasks")
    # 接触記録registration画面から「タスクも同時に保存する」を選んだ場合に紐付けられる。
    # 接触記録が削除されてもタスク自体は残したいのでSET_NULLにしている。
    contact_log = models.ForeignKey(
        ContactLog,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    title = models.CharField(max_length=200)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    assigned_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks"
    )
    deleted_at = models.DateTimeField(null=True, blank=True)  # 論理削除用

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "タスク"
        verbose_name_plural = "タスク"
