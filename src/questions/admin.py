from django.contrib import admin

from questions.models import QuestionResponse, QuestionTemplate
from questions.models.inferred_knowledge_state import InferredKnowledgeState
from questions.models.question_batch import QuestionBatch


@admin.register(QuestionTemplate)
class QuestionTemplateAdmin(admin.ModelAdmin):
    list_select_related = ("concept",)
    list_display = ("id", "concept", "question_type", "difficulty", "last_updated", "active")
    search_fields = ["id", "question_type", "template_text", "difficulty", "concept"]


@admin.register(QuestionBatch)
class QuestionBatchAdmin(admin.ModelAdmin):
    list_select_related = ("concept", "user")
    list_display = (
        "id",
        "user",
        "concept",
        "time_started",
        "time_taken_to_complete",
        "levels_progressed",
        "concept_completed",
    )
    search_fields = ["id", "user", "concept", "time_started", "time_taken_to_complete"]


@admin.register(QuestionResponse)
class QuestionResponseAdmin(admin.ModelAdmin):
    list_select_related = ("user", "question_template", "question_batch")
    list_display = (
        "id",
        "user",
        "question_template",
        "question_params",
        "question_batch",
        "correct",
        "response",
        "time_to_respond",
        "time_asked",
    )
    search_fields = [
        "id",
        "user",
        "question_template",
        "question_params",
        "question_batch",
        "response",
        "concept",
    ]


@admin.register(InferredKnowledgeState)
class InferredKnowledgeStateAdmin(admin.ModelAdmin):
    list_select_related = (
        "user",
        "concept",
    )
    list_display = ("id", "user", "concept", "mean", "std_dev", "last_updated")
    search_fields = ["id", "user", "concept"]
