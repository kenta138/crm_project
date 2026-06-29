from django.db import models
from accounts.models import User
from clients.models import Client


class ContactMethod(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '接触方法'
        verbose_name_plural = '接触方法'


class ContactLog(models.Model):
    METHOD_CHOICES = [
        ('phone', '電話'),
        ('email', 'メール'),
        ('line', 'LINE'),
        ('visit', '来訪'),
        ('online', '訪問'),
        ('other', 'その他'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contact_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='contact_logs')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='phone')
    date = models.DateTimeField()
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.client.name} - {self.title}'

    class Meta:
        verbose_name = '接触記録'
        verbose_name_plural = '接触記録'
        ordering = ['-date']