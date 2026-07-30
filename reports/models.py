from django.db import models
from accounts.models import User


class DailyReport(models.Model):
    STATUS_CHOICES = [
        ('ready', '完了'),
        ('pending', '生成中'),
        ('failed', '失敗'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_reports')
    report_date = models.DateField()
    content = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ready')
    error_message = models.TextField(blank=True)
    notified = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'{self.user.name} - {self.report_date}'

    class Meta:
        verbose_name = '日報'
        verbose_name_plural = '日報'
        unique_together = ('user', 'report_date')
        ordering = ['-report_date']