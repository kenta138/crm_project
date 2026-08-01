from pathlib import Path

import dj_database_url
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY")

DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "clients",
    "labels",
    "contacts",
    "tasks",
    "reports",
]

# ReportNotificationMiddlewareはmessagesフレームワーク(request._messages)を使うため、
# 必ずMessageMiddlewareより後ろに置く必要がある。順序を間違えるとMessageFailureが発生する。
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "reports.middleware.ReportNotificationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# dj_database_urlによりDATABASE_URLの形式に応じてSQLite/PostgreSQLを自動判別する。
# ローカル開発ではSQLite、Render上ではPostgreSQLのURLを.env(環境変数)で切り替える。
DATABASES = {"default": dj_database_url.config(default=config("DATABASE_URL"))}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ja"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_TZ = True

STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Render等のPaaS上でも自前でWebサーバー無しに静的ファイルを配信できるようWhiteNoiseを使用する
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# emailログイン・roleフィールドを持つ独自Userモデルを使用する(accounts/models.py参照)
AUTH_USER_MODEL = "accounts.User"

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/login/"

# 空(未設定)の場合は制限なし(誰でもサインアップ可能)。
# 社内利用に限定したい場合、環境変数にカンマ区切りで許可ドメインを設定する(例: "example.com,example.co.jp")。
SIGNUP_ALLOWED_EMAIL_DOMAINS = [
    d.strip().lower()
    for d in config("SIGNUP_ALLOWED_EMAIL_DOMAINS", default="").split(",")
    if d.strip()
]
# 日報生成(Gemini API)用のAPIキー。aistudio.google.com/apikeyで発行したものを使用する
# (Google CloudコンソールのAgent Platform Studioで発行したキーは組織ポリシーで弾かれることがあるため非推奨)。
GOOGLE_API_KEY = config("GOOGLE_API_KEY")
