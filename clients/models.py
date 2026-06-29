from django.db import models
from accounts.models import User
from labels.models import Label


class Client(models.Model):
    PHASE_CHOICES = [
        ('new', '新規'),
        ('negotiating', '商談中'),
        ('contracted', '契約済'),
        ('dormant', '休眠'),
    ]
    name = models.CharField(max_length=200)
    phase = models.CharField(max_length=20, choices=PHASE_CHOICES, default='new')
    labels = models.ManyToManyField(Label, blank=True, related_name='clients')
    assigned_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='clients'
    )
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    memo = models.TextField(blank=True)
    last_contact_date = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '取引先'
        verbose_name_plural = '取引先'