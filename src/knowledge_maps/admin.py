from django.contrib import admin

from knowledge_maps.models import KnowledgeMapModel


@admin.register(KnowledgeMapModel)
class QuestionModelAdmin(admin.ModelAdmin):
    pass
