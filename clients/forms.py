from django import forms
from .models import Client
from labels.models import Label


class ClientForm(forms.ModelForm):
    labels = forms.ModelMultipleChoiceField(
        queryset=Label.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='ラベル'
    )

    class Meta:
        model = Client
        fields = ['name', 'phase', 'assigned_user', 'phone', 'email', 'memo', 'labels']
        labels = {
            'name': '会社名',
            'phase': 'フェーズ',
            'assigned_user': '担当者',
            'phone': '電話番号',
            'email': 'メールアドレス',
            'memo': 'メモ',
        }