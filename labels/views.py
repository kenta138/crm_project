from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CategoryForm, LabelForm
from .models import Category, Label


def admin_required(view_func):
    """Adminロールのユーザーのみ実行を許可するデコレータ(clients/views.pyにも同名のものがあるが、
    アプリ間の依存を避けるためlabelsアプリ内に独立して定義している)。"""

    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != "admin":
            messages.error(request, "この画面はAdminのみアクセス可能です。")
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)

    return wrapper


@login_required
@admin_required
def label_top(request):
    """ラベル(Category)・項目(Label)の管理トップ画面。一覧表示と新規追加フォームを両方持つ。"""
    categories = Category.objects.prefetch_related("labels").all()
    category_form = CategoryForm()
    label_form = LabelForm()
    context = {
        "categories": categories,
        "category_form": category_form,
        "label_form": label_form,
    }
    return render(request, "labels/label_top.html", context)


@login_required
@admin_required
def category_new(request):
    """ラベル(Category)の新規追加。label_top画面のフォームからPOSTされる。"""
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "ラベルを追加しました。")
        else:
            messages.error(request, "ラベルの追加に失敗しました。")
    return redirect("label_top")


@login_required
@admin_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "ラベルを更新しました。")
            return redirect("label_top")
    else:
        form = CategoryForm(instance=category)
    return render(
        request, "labels/category_form.html", {"form": form, "title": "ラベル編集"}
    )


@login_required
@admin_required
def category_delete(request, pk):
    """ラベル(Category)の削除。取引先や接触記録と違い、マスタデータのため論理削除ではなく
    物理削除。関連する項目(Label)はモデル側のon_delete=CASCADEで連動して削除される。"""
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        category.delete()
        messages.success(request, "ラベルを削除しました。")
        return redirect("label_top")
    label_count = category.labels.count()
    return render(
        request,
        "labels/category_confirm_delete.html",
        {
            "category": category,
            "label_count": label_count,
        },
    )


@login_required
@admin_required
def label_new(request):
    """項目(Label)の新規追加。所属するラベル(Category)のIDはhiddenフィールドで渡される。"""
    if request.method == "POST":
        form = LabelForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "項目を追加しました。")
        else:
            messages.error(request, "項目の追加に失敗しました。")
    return redirect("label_top")


@login_required
@admin_required
def label_edit(request, pk):
    """項目(Label)の編集。有効/無効の切り替えもここのドロップダウンから行う
    (一覧画面には専用のトグル操作は無く、必ずこの編集画面を経由する)。"""
    label = get_object_or_404(Label, pk=pk)
    if request.method == "POST":
        form = LabelForm(request.POST, instance=label)
        if form.is_valid():
            form.save()
            messages.success(request, "項目を更新しました。")
            return redirect("label_top")
    else:
        form = LabelForm(instance=label)
    return render(
        request, "labels/label_form.html", {"form": form, "title": "項目編集"}
    )


@login_required
@admin_required
def label_delete(request, pk):
    """項目(Label)の削除。物理削除だが、取引先とのM2M中間テーブルの行が消えるだけで、
    取引先(Client)自体には影響しない。"""
    label = get_object_or_404(Label, pk=pk)
    if request.method == "POST":
        label.delete()
        messages.success(request, "項目を削除しました。")
        return redirect("label_top")
    client_count = label.clients.count()
    return render(
        request,
        "labels/label_confirm_delete.html",
        {
            "label": label,
            "client_count": client_count,
        },
    )
