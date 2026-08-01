from django.db import models

from accounts.models import User


# AIによる日報生成はバックグラウンドスレッドで非同期実行されるため、
# 生成中(pending)・完了(ready)・失敗(failed)の状態を持たせて進捗を追跡できるようにしている。
class DailyReport(models.Model):
    STATUS_CHOICES = [
        ("ready", "完了"),
        ("pending", "生成中"),
        ("failed", "失敗"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="daily_reports"
    )
    report_date = (
        models.DateField()
    )  # 日報の対象日(生成日時そのものはcreated_at/updated_atで別途持つ)
    content = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ready")
    error_message = models.TextField(blank=True)  # status='failed'の場合の失敗理由
    # 生成完了/失敗をダッシュボードの通知(ReportNotificationMiddleware)でまだ知らせていないかを表す。
    # 通知を出したらFalseに更新し、二重通知を防ぐ。
    notified = models.BooleanField(default=True)
    # 同じuser・report_dateの日報が既に存在する状態で再生成された場合にTrueになる。
    # report_list画面で「上書き済み」であることを表示するために使用する。
    regenerated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.name} - {self.report_date}"

    class Meta:
        verbose_name = "日報"
        verbose_name_plural = "日報"
        # 1ユーザー・1対象日につき日報は1件のみ(再生成時はupdate_or_createで上書きする)
        unique_together = ("user", "report_date")
        ordering = ["-report_date"]
