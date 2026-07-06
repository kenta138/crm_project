from django import forms
from django.utils import timezone
from datetime import timedelta
from .models import ContactLog
from clients.models import Client
from tasks.models import Task


class ContactLogForm(forms.ModelForm):
    date = forms.DateTimeField(
        label='接触日時',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        initial=timezone.now,
    )
    create_task = forms.BooleanField(
        required=False,
        label='タスクを同時作成する'
    )
    task_title = forms.CharField(
        required=False,
        label='タスクタイトル',
        max_length=200,
        widget=forms.TextInput(attrs={'id': 'id_task_title'})
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
        widgets = {
            'title': forms.TextInput(attrs={'id': 'id_title'}),
        }

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        from accounts.models import User
        self.fields['task_assigned_user'].queryset = User.objects.filter(is_active=True)

        if not self.instance.pk:
            self.fields['task_due_date'].initial = timezone.localdate() + timedelta(days=1)
            if request:
                self.fields['task_assigned_user'].initial = request.user