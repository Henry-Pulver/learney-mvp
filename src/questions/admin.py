from django.contrib import admin

from questions.models import QuestionResponseModel, QuestionTemplate


@admin.register(QuestionTemplate)
class QuestionTemplateModelAdmin(admin.ModelAdmin):
    list_select_related = ("concept",)
    list_display = ("id", "concept__name", "question_type", "difficulty", "last_updated")
    search_fields = ["id", "question_type", "template_text", "difficulty", "concept"]