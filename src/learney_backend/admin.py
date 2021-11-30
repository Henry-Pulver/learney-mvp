from django.contrib import admin

from learney_backend.models import ContentLinkPreview


@admin.register(ContentLinkPreview)
class QuestionModelAdmin(admin.ModelAdmin):
    list_display = ("concept", "title", "preview_last_updated", "url")
    search_fields = ("concept", "title", "preview_last_updated", "url")
