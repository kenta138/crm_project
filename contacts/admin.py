from django.contrib import admin
from .models import ContactMethod, ContactLog


@admin.register(ContactMethod)
class ContactMethodAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(ContactLog)
class ContactLogAdmin(admin.ModelAdmin):
    list_display = ('client', 'user', 'method', 'title', 'date')
    list_filter = ('method',)
    search_fields = ('title', 'content')
    