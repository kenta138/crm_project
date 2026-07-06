from django import forms
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from .models import User


class SignupForm(forms.ModelForm):
    password = forms.CharField(label='パスワード', widget=forms.PasswordInput)
    password_confirm = forms.CharField(label='パスワード（確認）', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['email', 'name']
        labels = {
            'email': 'メールアドレス',
            'name': '氏名',
        }

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        allowed_domains = settings.SIGNUP_ALLOWED_EMAIL_DOMAINS
        if allowed_domains:
            domain = email.split('@')[-1]
            if domain not in allowed_domains:
                raise forms.ValidationError('このメールアドレスのドメインではサインアップできません。')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('このメールアドレスは既に登録されています。')
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('パスワードが一致しません。')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'member'
        user.is_active = False
        if commit:
            user.save()
        return user