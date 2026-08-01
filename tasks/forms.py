from django import forms

from accounts.models import User
from clients.models import Client

from .models import Task


class TaskForm(forms.ModelForm):
    due_date = forms.DateField(
        required=False,
        label="期日",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    class Meta:
        model = Task
        fields = ["client", "title", "due_date", "status", "assigned_user"]
        labels = {
            "client": "取引先",
            "title": "タイトル",
            "status": "ステータス",
            "assigned_user": "担当者",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 論理削除済みの取引先・無効化されたユーザーは選択肢に出さない
        self.fields["client"].queryset = Client.objects.filter(deleted_at__isnull=True)
        self.fields["assigned_user"].queryset = User.objects.filter(is_active=True)
