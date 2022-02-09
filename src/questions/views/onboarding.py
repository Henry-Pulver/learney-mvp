from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from knowledge_maps.models import Concept, KnowledgeMapModel
from learned.models import LearnedModel
from questions.inference import GaussianParams
from questions.models.inferred_knowledge_state import InferredKnowledgeState

LEVEL_TO_KNOWLEDGE_STATE = {
    "New": lambda max_level: GaussianParams(1, max_level / 2),
    "Shaky": lambda max_level: GaussianParams(1 + max_level / 2, max_level / 2),
    "Known": lambda max_level: GaussianParams(1 + max_level, max_level / 2),
}


class UserOnboardingView(APIView):
    def post(self, request: Request, format=None) -> Response:
        """Updates user information for the question trial map based on Learney team member input.

        Hit up https://app.learney.me/question_admin to set these fields.
        """
        # try:
        user_id = request.data["user_id"]
        print(f"user_id: {user_id}")
        concept_levels = request.data["concept_levels"]
        print(f"concept_levels: {concept_levels}")
        user = User.objects.get(id=user_id)
        map = KnowledgeMapModel.objects.get(url_extension="questionsmap")

        learned_dict = {}

        concepts = {concept.cytoscape_id: concept for concept in Concept.objects.all()}
        max_levels = {
            concept.cytoscape_id: concept.max_difficulty_level for concept in concepts.values()
        }

        for concept_id, level in concept_levels.items():
            max_level = max_levels[concept_id]
            knowledge_state = LEVEL_TO_KNOWLEDGE_STATE[level](max_level)
            highest_level_achieved = (
                max_level if level == "Known" else max_level / 2 if level == "Shaky" else 0
            )

            existing_knowledge_states = InferredKnowledgeState.objects.filter(
                user=user, concept=concepts[concept_id]
            )
            if existing_knowledge_states.exists():
                inferred_knowledge_state = existing_knowledge_states[0]
                inferred_knowledge_state.mean = knowledge_state.mean
                inferred_knowledge_state.std_dev = knowledge_state.std_dev
                inferred_knowledge_state.highest_level_achieved = highest_level_achieved
                inferred_knowledge_state.save()
            else:
                InferredKnowledgeState.objects.create(
                    user=user,
                    concept=concepts[concept_id],
                    mean=knowledge_state.mean,
                    std_dev=knowledge_state.std_dev,
                    highest_level_achieved=highest_level_achieved,
                )
            print(
                f"concept={concepts[concept_id]},\t"
                f"mean={knowledge_state.mean},\t"
                f"std_dev={knowledge_state.std_dev},\t"
                f'highest_level={max_level if level == "Known" else max_level / 2 if level == "Shaky" else 0},'
            )

            if level == "Known":
                learned_dict[concept_id] = True

        LearnedModel.objects.create(map=map, user_id=user_id, learned_concepts=learned_dict)
        print(f"learned_dict={learned_dict}")

        return Response(
            {"Success": "User onboarding data entered successfully"}, status=status.HTTP_201_CREATED
        )
        # except Exception as e:
        #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
