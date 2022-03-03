from django.core.cache import cache
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from knowledge_maps.models import Concept
from questions.models.inferred_knowledge_state import InferredKnowledgeState
from questions.views.onboarding import LEVEL_TO_KNOWLEDGE_STATE


class ConceptInfoView(APIView):
    def get(self, request: Request, format=None) -> Response:
        user_id = request.GET["user_id"]
        concept_id = request.GET["concept_id"]
        # TODO: replace with use of InferredKnowledgeState.get()
        ks = cache.get(f"InferredKnowledgeState:concept:{concept_id}user:{user_id}")

        if ks is None:
            ks = InferredKnowledgeState.objects.filter(
                user__id=user_id, concept__cytoscape_id=concept_id
            ).prefetch_related("concept__question_templates")
            if not ks.exists():
                concept = Concept.objects.get(cytoscape_id=concept_id)
                max_level = concept.max_difficulty_level
                state = LEVEL_TO_KNOWLEDGE_STATE["New"](max_level)
                ks = InferredKnowledgeState.objects.create(
                    user=User.objects.get(id=user_id),
                    concept=concept,
                    mean=state.mean,
                    std_dev=state.std_dev,
                    highest_level_achieved=state.level,
                )
            else:
                ks = ks[0]
            cache.set(f"InferredKnowledgeState:concept:{concept_id}user:{user_id}", ks)
        return Response(
            {
                "level": ks.get_display_knowledge_level(new_batch=True),
                "max_level": ks.concept.max_difficulty_level,
            },
            status=status.HTTP_200_OK,
        )
