from django.contrib.auth.models import Group
from django.contrib import admin

from .models import Token

admin.site.unregister([Group])


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ('email', 'phone', 'otp', 'date_created', 'attempts', 'is_active')
    list_display_links = None
    search_fields = ('email', 'phone')
    list_filter = ('date_created', 'attempts', 'is_active')
    readonly_fields = ('email', 'phone', 'otp', 'date_created', 'attempts')
    ordering = ('-date_created',)
