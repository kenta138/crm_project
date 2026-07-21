from django import forms
from .models import Category, Label


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        labels = {
            'name': 'ラベル名',
        }


class LabelForm(forms.ModelForm):
    class Meta:
        model = Label
        fields = ['category', 'name', 'is_active']
        labels = {
            'name': '項目名',
            'category': 'ラベル',
            'is_active': '有効',
        }