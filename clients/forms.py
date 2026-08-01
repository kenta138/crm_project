from django import forms

from labels.models import Label

from .models import Client


class ClientForm(forms.ModelForm):
    # 無効化された項目(Label)は新規に選べないようクエリセットで除外する
    # (既に選択済みの無効項目は、client_form.html側でselected_label_idsを見て別途表示する)。
    # なお実際の見出し表示はclient_form.htmlが独自にカテゴリー(ラベル)ごとの
    # fieldsetでレンダリングするため、ここのlabel="ラベル"はテンプレート上では使われない。
    labels = forms.ModelMultipleChoiceField(
        queryset=Label.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="ラベル",
    )

    class Meta:
        model = Client
        fields = [
            "name",
            "custom_id",
            "phase",
            "assigned_user",
            "phone",
            "email",
            "memo",
            "labels",
        ]
        labels = {
            "name": "会社名",
            "custom_id": "取引先管理ID",
            "phase": "フェーズ",
            "assigned_user": "担当者",
            "phone": "電話番号",
            "email": "メールアドレス",
            "memo": "メモ",
        }
