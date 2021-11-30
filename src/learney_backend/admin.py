from django.contrib import admin

from learney_backend.models import ContentLinkPreview


@admin.register(ContentLinkPreview)
class QuestionModelAdmin(admin.ModelAdmin):
    pass
