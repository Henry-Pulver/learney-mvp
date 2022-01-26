from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from questions.models.inferred_knowledge_state import InferredKnowledgeState


class ConceptInfoView(APIView):
    def get(self, request: Request, format=None) -> Response:
        ks = InferredKnowledgeState.objects.get(
            user=request.GET["user_id"], concept__cytoscape_id=request.GET["concept_id"]
        ).select_related("concept__question_templates")
        return Response(
            {
                "level": ks.knowledge_level,
                "max_level": ks.concept.get_max_difficulty_level(),
            },
            status=status.HTTP_200_OK,
        )
