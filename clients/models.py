from django.db import models
from django.utils import timezone
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
    custom_id = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name='取引先管理ID'
    )
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

    @property
    def needs_follow_up(self):
        threshold = SystemSetting.get_solo().follow_up_threshold_days
        if self.last_contact_date is None:
            return True
        return (timezone.now() - self.last_contact_date).days >= threshold

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '取引先'
        verbose_name_plural = '取引先'
    
class SystemSetting(models.Model):
    follow_up_threshold_days = models.PositiveIntegerField(
        default=30,
        verbose_name='要フォロー判定日数',
        help_text='最終接触日からこの日数以上経過した取引先を「要フォロー」として一覧に表示します。'
    )
    report_prompt_template = models.TextField(
        default="""以下は{user_name}さんの{date}の接触記録です。
これをもとに、簡潔な日本語のビジネス日報を作成してください。

# 接触記録
{logs_text}

# 出力フォーマット
- 本日の活動概要
- 対応した取引先一覧
- 所感・課題
""",
        verbose_name='日報生成プロンプト',
        help_text='日報生成時にAIへ渡すプロンプトのテンプレートです。{user_name}・{date}・{logs_text}のプレースホルダーが使用できます。'
    )
    class Meta:
        verbose_name = 'システム設定'
        verbose_name_plural = 'システム設定'

    def __str__(self):
        return 'システム設定'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj