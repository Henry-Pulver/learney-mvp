from django.contrib import admin

from accounts.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "nickname", "picture", "locale", "in_questions_trial")
    search_fields = ["id", "name", "nickname", "given_name", "family_name", "picture", "locale"]
