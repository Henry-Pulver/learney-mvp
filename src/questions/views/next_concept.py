from typing import List

import numpy as np
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from goals.models import GoalModel
from knowledge_maps.models import Concept, KnowledgeMapModel
from learned.models import LearnedModel
from learney_web.settings import QUESTIONS_PREREQUISITE_DICT
from link_clicks.models import LinkClickModel
from questions.models.question_set import QuestionSet


class NextConceptView(APIView):
    def get(self, request: Request, format=None) -> Response:
        try:
            # Unpack inputs
            user_id = request.GET["user_id"]

            # Set seed in case randomness is required (for reproducibility)
            np.random.seed(1)

            prev_question_sets = QuestionSet.objects.filter(user__id=user_id).prefetch_related(
                "concept__direct_prerequisites"
            )
            # [0] Get the most recent question set
            if prev_question_sets.count() > 0:
                prev_question_set: QuestionSet = prev_question_sets.latest("time_started")

                if not prev_question_set.completed:  # [1.0] Concept is unfinished
                    return Response(
                        {"concept_id": prev_question_set.concept.cytoscape_id},
                        status=status.HTTP_200_OK,
                    )
                else:  # [2.0] Most recent question set, where the concept is finished
                    map = KnowledgeMapModel.objects.get(url_extension="questionsmap")

                    # [2.1] Find valid successor concepts
                    valid_next_concepts = get_valid_current_concept_ids(user_id, map)
                    if len(valid_next_concepts) == 0:
                        return Response({"concept_id": None}, status=status.HTTP_200_OK)
                    valid_successors: List[Concept] = list(
                        Concept.objects.filter(
                            direct_prerequisites=prev_question_set.concept,
                            cytoscape_id__in=valid_next_concepts,
                        )
                    )

                    if len(valid_successors) == 1:
                        return Response(
                            {"concept_id": valid_successors[0].cytoscape_id},
                            status=status.HTTP_200_OK,
                        )
                    elif len(valid_successors) > 2:
                        # [2.2] If multiple successors, go for the one which has had a content link clicked by this user before
                        return use_link_clicks_or_random(
                            map, user_id, [s.cytoscape_id for s in valid_successors]
                        )
                    else:  # [2.3] Otherwise try other valid concepts
                        return use_link_clicks_or_random(map, user_id, valid_next_concepts)

            else:  # [3.0] No past question sets
                map = KnowledgeMapModel.objects.get(url_extension="questionsmap")
                valid_next_concepts = get_valid_current_concept_ids(user_id, map)
                if len(valid_next_concepts) == 0:
                    return Response({"concept_id": None}, status=status.HTTP_200_OK)
                return use_link_clicks_or_random(map, user_id, valid_next_concepts)

            # Display an error if something goes wrong.
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


def get_valid_current_concept_ids(user_id: str, map: KnowledgeMapModel) -> List[str]:
    # [2.1.1] Towards their goal
    goals_queryset = GoalModel.objects.filter(user_id=user_id, map=map)
    goals = goals_queryset.latest("timestamp").goal_concepts if goals_queryset.count() > 0 else {}
    is_towards_goal = [
        any(concept_id in QUESTIONS_PREREQUISITE_DICT[goal_id] for goal_id in goals)
        for concept_id in QUESTIONS_PREREQUISITE_DICT
    ]

    # [2.1.2] All prerequisites learned
    learned_concepts_queryset = LearnedModel.objects.filter(user_id=user_id, map=map)
    learned_concepts = (
        learned_concepts_queryset.latest("timestamp").learned_concepts
        if learned_concepts_queryset.count() > 0
        else {}
    )
    prereqs_learned = [
        all(
            learned_concepts.get(prereq, False)
            for prereq in QUESTIONS_PREREQUISITE_DICT[concept_id]
        )
        for concept_id in QUESTIONS_PREREQUISITE_DICT
    ]
    # print(f"is_towards_goal: {is_towards_goal}")
    # print(f"prereqs_learned: {prereqs_learned}")
    output = [
        concept_id
        for count, concept_id in enumerate(QUESTIONS_PREREQUISITE_DICT)
        if prereqs_learned[count] and is_towards_goal[count]
    ]
    return output


def use_link_clicks_or_random(
    map: KnowledgeMapModel, user_id: str, possible_concept_ids: List[str]
):
    relevant_link_clicks = LinkClickModel.objects.filter(
        map=map, user_id=user_id, concept_id__in=possible_concept_ids
    )
    if relevant_link_clicks.count() > 0:
        print(relevant_link_clicks.latest("timestamp").concept_id)
        return Response(
            {"concept_id": relevant_link_clicks.latest("timestamp").concept_id},
            status=status.HTTP_200_OK,
        )
    else:
        return Response(
            {"concept_id": np.random.choice(possible_concept_ids)}, status=status.HTTP_200_OK
        )
