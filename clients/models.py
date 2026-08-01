from django.db import models
from django.utils import timezone

from accounts.models import User
from labels.models import Label


class Client(models.Model):
    # 取引先の営業フェーズ。client_list画面のフィルタ・サマリーで使用する。
    PHASE_CHOICES = [
        ("new", "新規"),
        ("negotiating", "商談中"),
        ("contracted", "契約済"),
        ("dormant", "休眠"),
    ]
    name = models.CharField(max_length=200)
    # システムが自動採番するid(PK)とは別に、ユーザーが自由に設定できる取引先管理番号。
    # 既存の社内管理番号と紐付けたい場合などに使う想定で、空でも良いがユニーク制約は付ける。
    custom_id = models.CharField(
        max_length=50, unique=True, blank=True, null=True, verbose_name="取引先管理ID"
    )
    phase = models.CharField(max_length=20, choices=PHASE_CHOICES, default="new")
    labels = models.ManyToManyField(Label, blank=True, related_name="clients")
    assigned_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="clients"
    )
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    memo = models.TextField(blank=True)
    # 接触記録(ContactLog)が登録・削除されるたびにcontacts側のビューから更新される非正規化フィールド。
    # 一覧画面での並び替え・フィルタを高速化するために都度計算せず保持している。
    last_contact_date = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)  # 論理削除用

    @property
    def needs_follow_up(self):
        """最終接触日から一定日数(管理者設定の閾値)以上経過していれば要フォローと判定する。"""
        threshold = SystemSetting.get_solo().follow_up_threshold_days
        if self.last_contact_date is None:
            return True
        return (timezone.now() - self.last_contact_date).days >= threshold

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "取引先"
        verbose_name_plural = "取引先"


# アプリ全体で共有する設定値を1レコードだけ保持するシングルトンモデル。
# 複数レコードが作られると意味が曖昧になるため、save()でPKを1に固定して上書きを強制している。
class SystemSetting(models.Model):
    follow_up_threshold_days = models.PositiveIntegerField(
        default=30,
        verbose_name="要フォロー判定日数",
        help_text="最終接触日からこの日数以上経過した取引先を「要フォロー」として一覧に表示します。",
    )
    # 日報生成AIへ渡すプロンプトをDjango管理画面から編集できるようにするためのテンプレート。
    # {user_name}・{date}・{logs_text}はreports/views.pyの_build_prompt()でformat()展開される。
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
        verbose_name="日報生成プロンプト",
        help_text="日報生成時にAIへ渡すプロンプトのテンプレートです。{user_name}・{date}・{logs_text}のプレースホルダーが使用できます。",
    )

    class Meta:
        verbose_name = "システム設定"
        verbose_name_plural = "システム設定"

    def __str__(self):
        return "システム設定"

    def save(self, *args, **kwargs):
        # 常にpk=1に固定することで、SystemSettingが複数作られないようにする(シングルトンパターン)。
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        """唯一のSystemSettingインスタンスを取得する。存在しなければデフォルト値で新規作成する。"""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
