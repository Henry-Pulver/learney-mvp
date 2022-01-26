from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from questions.models.inferred_knowledge_state import InferredKnowledgeState

INIT_MEAN = 1.0
INIT_STD_DEV = 1.0


class ConceptInfoView(APIView):
    def get(self, request: Request, format=None) -> Response:
        user_id = request.GET["user_id"]
        concept_id = request.GET["concept_id"]
        ks = InferredKnowledgeState.objects.filter(
            user=user_id, concept__cytoscape_id=concept_id
        ).select_related("concept__question_templates")
        if not ks.exists():
            ks = InferredKnowledgeState.objects.create(
                user=user_id,
                concept=concept_id,
                mean=INIT_MEAN,
                std_dev=INIT_STD_DEV,
            )
        return Response(
            {
                "level": ks.knowledge_level,
                "max_level": ks.concept.get_max_difficulty_level(),
            },
            status=status.HTTP_200_OK,
        )
