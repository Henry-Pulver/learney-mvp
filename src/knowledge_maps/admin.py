from django.contrib import admin

from knowledge_maps.models import KnowledgeMapModel


@admin.register(KnowledgeMapModel)
class QuestionModelAdmin(admin.ModelAdmin):
    list_display = ("url_extension", "author_user_id", "s3_key", "last_updated")
    search_fields = ["url_extension", "author_user_id", "s3_key"]
