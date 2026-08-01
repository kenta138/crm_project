from datetime import timedelta

from django import forms
from django.utils import timezone

from clients.models import Client
from tasks.models import Task

from .models import ContactLog


class ContactLogForm(forms.ModelForm):
    date = forms.DateTimeField(
        label="接触日時",
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
        ),
        initial=timezone.now,
    )
    # ここから4つ(task_*)はContactLogモデル自体のフィールドではなく、
    # 新規登録時に「タスクも同時に保存する」を選んだ場合にのみ使う一時的な入力項目。
    # 編集時はモデルに存在しないため__init__内で毎回削除する(下記else節)。
    task_title = forms.CharField(
        required=False,
        label="タスクタイトル",
        max_length=200,
        widget=forms.TextInput(attrs={"id": "id_task_title"}),
    )
    task_due_date = forms.DateField(
        required=False,
        label="タスク期日",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    task_assigned_user = forms.ModelChoiceField(
        required=False, queryset=None, label="タスク担当者"
    )

    class Meta:
        model = ContactLog
        fields = ["client", "method", "date", "title", "content"]
        labels = {
            "client": "取引先",
            "method": "接触方法",
            "title": "タイトル",
            "content": "内容",
        }
        widgets = {
            # contact_form.htmlのJSがこのidを見て、タイトル入力からタスクタイトルへ自動コピーする
            "title": forms.TextInput(attrs={"id": "id_title"}),
        }

    def __init__(self, *args, **kwargs):
        # requestはビュー(contact_new)から明示的に渡される。タスク担当者の初期値に
        # ログインユーザーをセットするためだけに必要で、フォーム自体の保存処理には使わない。
        request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        from accounts.models import User

        self.fields["task_assigned_user"].queryset = User.objects.filter(is_active=True)

        if not self.instance.pk:
            # 新規登録時のみ: タスク期日はデフォルトで翌日、担当者はログインユーザーを初期値にする
            self.fields["task_due_date"].initial = timezone.localdate() + timedelta(
                days=1
            )
            if request:
                self.fields["task_assigned_user"].initial = request.user
        else:
            # 編集時はタスク同時作成の概念自体が無いため、関連フィールドをフォームから完全に除外する
            del self.fields["task_title"]
            del self.fields["task_due_date"]
            del self.fields["task_assigned_user"]
