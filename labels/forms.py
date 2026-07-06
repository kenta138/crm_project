from django import forms
from .models import Category, Label


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        labels = {
            'name': 'カテゴリー名',
        }


class LabelForm(forms.ModelForm):
    class Meta:
        model = Label
        fields = ['category', 'name', 'is_active']
        labels = {
            'name': 'ラベル名',
            'category': 'カテゴリー',
            'is_active': '有効',
        }