from django import forms
from .models import Task
from clients.models import Client
from accounts.models import User


class TaskForm(forms.ModelForm):
    due_date = forms.DateField(
        required=False,
        label='期日',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    class Meta:
        model = Task
        fields = ['client', 'title', 'due_date', 'status', 'assigned_user']
        labels = {
            'client': '取引先',
            'title': 'タイトル',
            'status': 'ステータス',
            'assigned_user': '担当者',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = Client.objects.filter(deleted_at__isnull=True)
        self.fields['assigned_user'].queryset = User.objects.filter(is_active=True)