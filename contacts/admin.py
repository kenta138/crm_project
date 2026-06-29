from django.contrib import admin
from .models import ContactLog


@admin.register(ContactLog)
class ContactLogAdmin(admin.ModelAdmin):
    list_display = ('client', 'user', 'method', 'title', 'date')
    list_filter = ('method',)
    search_fields = ('title', 'content')