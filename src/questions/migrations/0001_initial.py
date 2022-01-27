# Generated by Django 3.2.2 on 2022-01-27 12:42

import uuid

import django.db.models.deletion
from django.db import migrations, models

import questions.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0005_user_in_questions_trial"),
    ]

    operations = [
        migrations.CreateModel(
            name="QuestionTemplate",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, help_text="Unique id", primary_key=True, serialize=False
                    ),
                ),
                (
                    "difficulty",
                    models.FloatField(
                        help_text="Question difficulty for the concept. Initially set by an expert, but will subsequently be inferred from data. A relative scale, with 0 the lowest possible and as many difficulty levels as is deemed makes sense by the expert.",
                        validators=[questions.validators.integer_is_positive],
                    ),
                ),
                (
                    "question_type",
                    models.TextField(
                        help_text="Text for question template - generates full question",
                        validators=[questions.validators.not_null],
                    ),
                ),
                (
                    "template_text",
                    models.TextField(
                        help_text="Text for question template - generates full question",
                        max_length=16384,
                        validators=[questions.validators.not_null],
                    ),
                ),
                (
                    "correct_answer_letter",
                    models.CharField(
                        choices=[
                            ("a", "a_lower"),
                            ("A", "A_upper"),
                            ("b", "b_lower"),
                            ("B", "B_upper"),
                            ("c", "c_lower"),
                            ("C", "C_upper"),
                            ("d", "d_lower"),
                            ("D", "D_upper"),
                        ],
                        help_text="Answer option (a, b, c or d) which is the correct answer to the question",
                        max_length=1,
                    ),
                ),
                (
                    "active",
                    models.BooleanField(
                        default=False,
                        help_text="If questions from the template should be used onthe live site - broken questions should be deactivated until they're fixed!",
                    ),
                ),
                ("last_updated", models.DateTimeField(auto_now=True)),
                (
                    "concept",
                    models.ForeignKey(
                        help_text="Concept that the question corresponds to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="question_templates",
                        to="knowledge_maps.concept",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="QuestionSet",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, help_text="Unique id", primary_key=True, serialize=False
                    ),
                ),
                (
                    "time_started",
                    models.DateTimeField(
                        auto_now_add=True, help_text="Time that the question set was started"
                    ),
                ),
                (
                    "time_taken_to_complete",
                    models.DateTimeField(
                        default=None,
                        help_text="Time after the question set was started that it was completed",
                        null=True,
                    ),
                ),
                (
                    "completed",
                    models.BooleanField(
                        default=False,
                        help_text="Whether the user answered all the questions in the set or not",
                    ),
                ),
                (
                    "level_at_start",
                    models.IntegerField(
                        help_text="The concept level the user started the question set at"
                    ),
                ),
                (
                    "initial_knowledge_mean",
                    models.FloatField(
                        help_text="Mean of the user's knowledge state when they started the question set"
                    ),
                ),
                (
                    "initial_knowledge_std_dev",
                    models.FloatField(
                        help_text="Standard deviation of the user's knowledge state when they started the question set"
                    ),
                ),
                (
                    "levels_progressed",
                    models.IntegerField(
                        default=0,
                        help_text="How many levels the user progressed in this question batch",
                    ),
                ),
                (
                    "concept_completed",
                    models.BooleanField(
                        default=False,
                        help_text="Whether the highest level of the concept was achieved in this question set",
                    ),
                ),
                (
                    "session_id",
                    models.TextField(help_text="session_id of the session the response was from"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        help_text="User whose response this is",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="question_responses",
                        to="accounts.user",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="QuestionResponse",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, help_text="Unique id", primary_key=True, serialize=False
                    ),
                ),
                (
                    "question_params",
                    models.JSONField(
                        help_text="question parameter values chosen from the template parameters"
                    ),
                ),
                (
                    "response",
                    models.TextField(
                        default=None,
                        help_text="Response given to the question. Null if yet to be answered",
                        max_length=1024,
                        null=True,
                    ),
                ),
                (
                    "correct",
                    models.BooleanField(
                        default=None,
                        help_text="Was the response correct? Null if not yet answered.",
                        null=True,
                    ),
                ),
                (
                    "session_id",
                    models.TextField(help_text="session_id of the session the response was from"),
                ),
                (
                    "time_to_respond",
                    models.DurationField(
                        help_text="Time it took for the user to respond to the question. Measured on the backend. Currently measured, but not used",
                        null=True,
                    ),
                ),
                (
                    "time_asked",
                    models.DateTimeField(
                        auto_now_add=True, help_text="Time that the question was asked"
                    ),
                ),
                (
                    "question_set",
                    models.ForeignKey(
                        help_text="The question set this question corresponds to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="responses",
                        to="questions.questionset",
                    ),
                ),
                (
                    "question_template",
                    models.ForeignKey(
                        help_text="question template this was a response to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="responses",
                        to="questions.questiontemplate",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        help_text="User whose response this is",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="responses",
                        to="accounts.user",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="InferredKnowledgeState",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, help_text="Unique id", primary_key=True, serialize=False
                    ),
                ),
                (
                    "mean",
                    models.FloatField(
                        help_text="Mean of the inferred knowledge state distribution"
                    ),
                ),
                (
                    "std_dev",
                    models.FloatField(
                        help_text="Standard deviation of the inferred knowledge state distribution"
                    ),
                ),
                (
                    "last_updated",
                    models.DateTimeField(
                        auto_now=True, help_text="Time that the knowledge state was last updated"
                    ),
                ),
                (
                    "concept",
                    models.ForeignKey(
                        help_text="The concept that this knowledge state refers to",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="user_knowledge_states",
                        to="knowledge_maps.concept",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        help_text="User who this knowledge state refers to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="knowledge_states",
                        to="accounts.user",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="inferredknowledgestate",
            constraint=models.UniqueConstraint(
                fields=("user", "concept"), name="unique_user_concept"
            ),
        ),
    ]
