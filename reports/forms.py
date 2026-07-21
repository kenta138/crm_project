from django import forms
from .models import DailyReport


class DailyReportForm(forms.ModelForm):
    class Meta:
        model = DailyReport
        fields = ['content']
        labels = {
            'content': '日報内容',
        }
        widgets = {
            'content': forms.Textarea(attrs={'rows': 20}),
        }