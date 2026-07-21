from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Category, Label
from .forms import CategoryForm, LabelForm


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            messages.error(request, 'この画面はAdminのみアクセス可能です。')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@admin_required
def label_top(request):
    categories = Category.objects.prefetch_related('labels').all()
    category_form = CategoryForm()
    label_form = LabelForm()
    context = {
        'categories': categories,
        'category_form': category_form,
        'label_form': label_form,
    }
    return render(request, 'labels/label_top.html', context)


@login_required
@admin_required
def category_new(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'ラベルを追加しました。')
        else:
            messages.error(request, 'ラベルの追加に失敗しました。')
    return redirect('label_top')


@login_required
@admin_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'ラベルを更新しました。')
            return redirect('label_top')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'labels/category_form.html', {'form': form, 'title': 'ラベル編集'})


@login_required
@admin_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'ラベルを削除しました。')
        return redirect('label_top')
    label_count = category.labels.count()
    return render(request, 'labels/category_confirm_delete.html', {
        'category': category,
        'label_count': label_count,
    })


@login_required
@admin_required
def label_new(request):
    if request.method == 'POST':
        form = LabelForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '項目を追加しました。')
        else:
            messages.error(request, '項目の追加に失敗しました。')
    return redirect('label_top')


@login_required
@admin_required
def label_edit(request, pk):
    label = get_object_or_404(Label, pk=pk)
    if request.method == 'POST':
        form = LabelForm(request.POST, instance=label)
        if form.is_valid():
            form.save()
            messages.success(request, '項目を更新しました。')
            return redirect('label_top')
    else:
        form = LabelForm(instance=label)
    return render(request, 'labels/label_form.html', {'form': form, 'title': '項目編集'})


@login_required
@admin_required
def label_delete(request, pk):
    label = get_object_or_404(Label, pk=pk)
    if request.method == 'POST':
        label.delete()
        messages.success(request, '項目を削除しました。')
        return redirect('label_top')
    client_count = label.clients.count()
    return render(request, 'labels/label_confirm_delete.html', {
        'label': label,
        'client_count': client_count,
    })


@login_required
@admin_required
def label_toggle(request, pk):
    label = get_object_or_404(Label, pk=pk)
    if request.method == 'POST':
        label.is_active = not label.is_active
        label.save()
        status = '有効' if label.is_active else '無効'
        messages.success(request, f'項目を{status}にしました。')
    return redirect('label_top')