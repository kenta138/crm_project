from django import forms

from .models import DailyReport


# AIが生成したcontentを人が手直しできるようにするための、シンプルな1フィールドのみのフォーム。
class DailyReportForm(forms.ModelForm):
    class Meta:
        model = DailyReport
        fields = ["content"]
        labels = {
            "content": "日報内容",
        }
        widgets = {
            "content": forms.Textarea(attrs={"rows": 20}),
        }
