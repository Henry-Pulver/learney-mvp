import numpy as np
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from questions.models import QuestionResponse, QuestionTemplate
from questions.models.inferred_knowledge_state import InferredKnowledgeState
from questions.models.question_set import QuestionSet
from questions.question_selection import difficulty_terms, get_knowledge_level, novelty_terms
from questions.template_parser import parse_params, question_from_template, sample_params
from questions.utils import get_today


class QuestionSetView(APIView):
    def get(self, request: Request, format=None) -> Response:
        concept_id = request.GET["concept_id"]
        user_id = request.GET["user_id"]
        session_id = request.GET["session_id"]
        prev_set = QuestionSet.objects.filter(completed=False, time_started__gte=get_today())
        if prev_set.exists():
            question_set = prev_set[0]
        else:
            ks = InferredKnowledgeState.objects.get(user=user_id, concept__cytoscape_id=concept_id)
            question_set = QuestionSet.objects.create(
                user=user_id,
                level_at_start=get_knowledge_level(ks),
                session_id=session_id,
            )

        # TODO: Track with Mixpanel

        return Response(
            {
                "id": question_set.id,
            },
            status=status.HTTP_200_OK,
        )


class QuestionView(APIView):
    def get(self, request: Request, format=None) -> Response:
        try:
            concept_id = request.GET["concept_id"]
            user_id = request.GET["user_id"]
            question_set = QuestionSet.objects.get(
                id=request.GET["question_set_id"]
            ).selected_related("responses")

            knowledge_state = InferredKnowledgeState.objects.get(
                user=user_id, concept__cytoscape_id=concept_id
            ).select_related("user")

            template_options = QuestionTemplate.objects.filter(
                concept__cytoscape_id=concept_id
            ).prefetch_related("responses")

            # Calculate the weights. Once normalised, these form the categorical
            #  distribution over question templates
            question_weights = difficulty_terms(template_options, knowledge_state) * novelty_terms(
                template_options, knowledge_state.user, question_set
            )

            # Choose the template that's going to be used!
            question_seen_before = True
            while question_seen_before:
                chosen_template = np.random.choice(
                    template_options, p=question_weights / np.mean(question_weights)
                )
                question_param_options, remaining_text = parse_params(chosen_template.template_text)
                sampled_params = sample_params(question_param_options)
                # Make 100% sure it's not been seen already in this question set!
                question_seen_before = question_set.responses.filter(
                    question_template=chosen_template, question_params=sampled_params
                ).exists()

            question = question_from_template(chosen_template, sampled_params)

            # Track the question was sent in the DB
            QuestionResponse.objects.create(
                user=user_id,
                question_template=chosen_template,
                question_params=sampled_params,
                question_set=question_set,
                session_id=request.GET["session_id"],
                response=None,
                correct=None,
                time_to_respond=None,
            )

            # TODO: Track with Mixpanel

            return Response(question, status=status.HTTP_200_OK)
        except KeyError as error:
            return Response(str(error), status=status.HTTP_400_BAD_REQUEST)
