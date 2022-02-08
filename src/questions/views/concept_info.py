from django.core.cache import cache
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from knowledge_maps.models import Concept
from questions.inference import GaussianParams
from questions.models.inferred_knowledge_state import InferredKnowledgeState

INIT_MEAN = 1.0
INIT_STD_DEV = 1.0


class ConceptInfoView(APIView):
    def get(self, request: Request, format=None) -> Response:
        user_id = request.GET["user_id"]
        concept_id = request.GET["concept_id"]
        ks = cache.get(f"InferredKnowledgeState:concept:{concept_id}user:{user_id}")

        if ks is None:
            ks = InferredKnowledgeState.objects.filter(
                user__id=user_id, concept__cytoscape_id=concept_id
            ).prefetch_related("concept__question_templates")
            if not ks.exists():
                ks = InferredKnowledgeState.objects.create(
                    user=User.objects.get(id=user_id),
                    concept=Concept.objects.get(cytoscape_id=concept_id),
                    mean=INIT_MEAN,
                    std_dev=INIT_STD_DEV,
                    highest_level_achieved=GaussianParams(INIT_MEAN, INIT_STD_DEV).level,
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
