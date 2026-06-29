from django import forms
from django.utils import timezone
from .models import ContactLog
from clients.models import Client
from tasks.models import Task


class ContactLogForm(forms.ModelForm):
    date = forms.DateTimeField(
        label='接触日時',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        initial=timezone.now,
    )
    create_task = forms.BooleanField(
        required=False,
        label='タスクを同時作成する'
    )
    task_title = forms.CharField(
        required=False,
        label='タスクタイトル',
        max_length=200
    )
    task_due_date = forms.DateField(
        required=False,
        label='タスク期日',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    task_assigned_user = forms.ModelChoiceField(
        required=False,
        queryset=None,
        label='タスク担当者'
    )

    class Meta:
        model = ContactLog
        fields = ['client', 'method', 'date', 'title', 'content']
        labels = {
            'client': '取引先',
            'method': '接触方法',
            'title': 'タイトル',
            'content': '内容',
        }

    def __init__(self, *args, **kwargs):
        from accounts.models import User
        super().__init__(*args, **kwargs)
        self.fields['task_assigned_user'].queryset = User.objects.filter(is_active=True)