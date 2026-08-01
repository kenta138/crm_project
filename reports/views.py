import threading
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from google import genai

from clients.models import SystemSetting
from contacts.models import ContactLog

from .forms import DailyReportForm
from .models import DailyReport


def can_view_all(user):
    """他ユーザー分の日報も閲覧できるロールかどうかを判定する。"""
    return user.role in ["admin", "manager"]


def _build_prompt(user, report_date, contact_logs):
    """AIに渡す日報生成プロンプトを組み立てる。テンプレート本文はDjango管理画面の
    SystemSetting.report_prompt_templateで編集可能で、{user_name}/{date}/{logs_text}を
    str.format()で埋め込む。"""
    lines = [
        f"- {log.client.name}様（{log.get_method_display()}）: {log.title}\n  {log.content}"
        for log in contact_logs
    ]
    logs_text = "\n".join(lines)

    template = SystemSetting.get_solo().report_prompt_template
    return template.format(
        user_name=user.name,
        date=report_date.strftime("%Y年%m月%d日"),
        logs_text=logs_text,
    )


@login_required
def report_list(request):
    """日報一覧。Admin・Managerは全ユーザー分、Memberは自分の日報のみ表示する。"""
    reports = DailyReport.objects.select_related("user")
    if not can_view_all(request.user):
        reports = reports.filter(user=request.user)
    reports = reports.order_by("-report_date")

    paginator = Paginator(reports, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "reports/report_list.html", {"page_obj": page_obj})


def _generate_report_async(user_id, report_date, was_existing):
    """バックグラウンドスレッド上で実際にGemini APIを呼び出し、日報を生成する処理本体。
    report_generate()から非同期(daemon thread)で呼び出されるため、
    ここで例外を捕まえてDailyReport.status='failed'に保存し、リクエストへは何も返さない。
    完了・失敗の通知はReportNotificationMiddleware(reports/middleware.py)が
    次のリクエスト時にDailyReport.notifiedを見て行う。"""
    contact_logs = (
        ContactLog.objects.filter(
            user_id=user_id, date__date=report_date, deleted_at__isnull=True
        )
        .select_related("client")
        .order_by("date")
    )

    if not contact_logs.exists():
        DailyReport.objects.update_or_create(
            user_id=user_id,
            report_date=report_date,
            defaults={
                "status": "failed",
                "error_message": f'{report_date.strftime("%Y/%m/%d")}の接触記録が見つかりません。',
                "notified": False,
            },
        )
        return

    user = contact_logs.first().user
    prompt = _build_prompt(user, report_date, contact_logs)

    try:
        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
        )
        DailyReport.objects.update_or_create(
            user_id=user_id,
            report_date=report_date,
            defaults={
                "content": response.text,
                "status": "ready",
                "error_message": "",
                "notified": False,
                "regenerated": was_existing,
            },
        )
    except Exception as e:
        DailyReport.objects.update_or_create(
            user_id=user_id,
            report_date=report_date,
            defaults={
                "status": "failed",
                "error_message": str(e),
                "notified": False,
            },
        )


@login_required
def report_generate(request):
    """日報生成の起点となるビュー。ダッシュボードの生成フォームからPOSTされる想定で、
    その場でAI応答を待たずにバックグラウンドスレッドを起動してすぐダッシュボードへ戻す
    (非同期化により、生成中もユーザーは他の操作を続けられる)。
    GET時は専用の生成画面を持たないため、単純にダッシュボードへリダイレクトする。"""
    if request.method == "POST":
        date_str = request.POST.get("report_date")
        try:
            report_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            report_date = timezone.localdate()

        # 既にready状態の日報が存在する場合は「上書き(再生成)」として扱い、
        # 一覧画面でその旨を表示するためのフラグとして後段の非同期処理に渡す。
        was_existing = DailyReport.objects.filter(
            user=request.user, report_date=report_date, status="ready"
        ).exists()

        # 生成開始時点で先にstatus='pending'のレコードを作っておくことで、
        # 生成中に日報詳細/編集画面へ直接アクセスされても「まだ準備できていません」と
        # 案内できるようにする(report_detail/report_editのstatusチェック参照)。
        DailyReport.objects.update_or_create(
            user=request.user,
            report_date=report_date,
            defaults={"status": "pending", "error_message": "", "notified": True},
        )

        # daemon=Trueにすることで、Webサーバープロセスの終了時にスレッドが残り続けない
        # ようにしている。Celery等のジョブキューを使わない簡易な非同期実装のため、
        # プロセス再起動時は生成中だったジョブの結果が失われる点に注意。
        thread = threading.Thread(
            target=_generate_report_async,
            args=(request.user.id, report_date, was_existing),
            daemon=True,
        )
        thread.start()

        messages.success(
            request,
            f'{report_date.strftime("%Y/%m/%d")}の日報生成を開始しました。完了次第お知らせします。',
        )
        return redirect("dashboard")

    return redirect("dashboard")


@login_required
def report_detail(request, pk):
    """日報の詳細表示。本人以外はAdmin・Managerのみ閲覧可能。
    生成中(pending)・失敗(failed)の状態ではまだ表示するcontentが無いため一覧へ差し戻す。"""
    report = get_object_or_404(DailyReport, pk=pk)
    if report.user != request.user and not can_view_all(request.user):
        messages.error(request, "この日報を閲覧する権限がありません。")
        return redirect("report_list")
    if report.status != "ready":
        messages.error(request, "この日報はまだ準備できていません。")
        return redirect("report_list")
    return render(request, "reports/report_detail.html", {"report": report})


@login_required
def report_edit(request, pk):
    """日報の編集。他人の日報は編集不可(閲覧許可のcan_view_allとは別の、本人限定のチェック)。"""
    report = get_object_or_404(DailyReport, pk=pk)
    if report.user != request.user:
        messages.error(request, "この日報を編集する権限がありません。")
        return redirect("report_detail", pk=pk)
    if report.status != "ready":
        messages.error(request, "この日報はまだ準備できていません。")
        return redirect("report_list")

    if request.method == "POST":
        form = DailyReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, "日報を更新しました。")
            return redirect("report_detail", pk=pk)
    else:
        form = DailyReportForm(instance=report)

    return render(
        request,
        "reports/report_form.html",
        {
            "form": form,
            "report_date": report.report_date,
            "title": "日報編集",
            "form_action": reverse("report_edit", args=[pk]),
        },
    )
