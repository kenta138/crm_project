from django import forms

from .models import Category, Label


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]
        labels = {
            "name": "ラベル名",
        }


class LabelForm(forms.ModelForm):
    # モデル上はBooleanField(チェックボックス)だが、編集画面では有効/無効を
    # プルダウンで明示的に選ばせたいため、TypedChoiceFieldで上書きしている。
    # choicesのキーはPythonのTrue/Falseだが、POST時は文字列"True"/"False"で届くため
    # coerceで明示的にbool変換する必要がある。
    is_active = forms.TypedChoiceField(
        choices=[(True, "有効"), (False, "無効")],
        coerce=lambda x: x == "True",
        label="有効",
        widget=forms.Select,
    )

    class Meta:
        model = Label
        fields = ["category", "name", "is_active"]
        labels = {
            "name": "項目名",
            "category": "ラベル",
        }
