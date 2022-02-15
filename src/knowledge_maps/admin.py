from django.contrib import admin

from knowledge_maps.models import KnowledgeMapModel


@admin.register(KnowledgeMapModel)
class MapModelAdmin(admin.ModelAdmin):
    list_display = ("url_extension", "title", "author_user_id", "s3_key", "last_updated")
    search_fields = ["title", "description", "url_extension", "author_user_id", "s3_key"]
