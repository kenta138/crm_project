from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import SignupForm


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("login")


def signup(request):
    # SignupForm.save()内でis_active=Falseとして保存されるため、
    # ここで作成したユーザーは管理者がDjango管理画面でis_activeをTrueにするまでログインできない。
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "サインアップが完了しました。管理者の承認後にログインできます。",
            )
            return redirect("login")
    else:
        form = SignupForm()
    return render(request, "accounts/signup.html", {"form": form})
