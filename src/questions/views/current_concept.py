import random
from typing import List
from uuid import UUID

from django.db.models import QuerySet
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from goals.models import GoalModel
from knowledge_maps.models import KnowledgeMapModel
from learned.models import LearnedModel
from learney_web.settings import QUESTIONS_PREREQUISITE_DICT
from link_clicks.models import LinkClickModel
from questions.models.question_batch import QuestionBatch


class CurrentConceptView(APIView):
    def get(self, request: Request, format=None) -> Response:
        """ONLY VALID FOR QUESTIONS ENDPOINT!

        Gets the concept that we suggest the user work on.

        It first gets the concept of the previous question set you did (if that concept
        isn't completed already). Then it looks for valid concepts given your goals
        and what you've learned and picks based on content link clicks and if you haven't
        clicked any content - it picks randomly from these.

        If there is no goal set then it returns None.
        """
        try:
            user_id = request.GET["user_id"]
            map_uuid = request.GET["map_uuid"]

            questions_map_id: UUID = KnowledgeMapModel.get(url_extension="questionsmap").unique_id  # type: ignore
            if map_uuid != str(questions_map_id):
                return Response(status=status.HTTP_400_BAD_REQUEST)

            # Set seed in case randomness is required (for reproducibility)
            random.seed(1)

            valid_current_concepts = get_valid_current_concept_ids(user_id, map_uuid)

            if len(valid_current_concepts) == 0:
                print("0.0 No valid concepts found")
                return Response({"concept_id": None}, status=status.HTTP_200_OK)

            prev_question_batches: QuerySet[QuestionBatch] = QuestionBatch.objects.filter(
                user__id=user_id
            ).prefetch_related("concept__direct_prerequisites")
            if prev_question_batches.count() > 0:
                # [1.0] Get the most recent question batch
                prev_question_batch: QuestionBatch = prev_question_batches.latest("time_started")

                if (
                    prev_question_batch.concept.cytoscape_id in valid_current_concepts
                ):  # [2.0] Concept prev question batch is a valid current concept
                    print("2.0 Concept from prev batch is valid")
                    return Response(
                        {"concept_id": prev_question_batch.concept.cytoscape_id},
                        status=status.HTTP_200_OK,
                    )

                # [2.1] If not valid, it may not be valid because it's been learned!
                learned_model = LearnedModel.get(user_id, map_uuid)
                learned_concepts = learned_model.learned_concepts if learned_model else {}
                prev_concept_id: str = prev_question_batch.concept.cytoscape_id

                if learned_concepts.get(prev_concept_id, False):  # Check if prev concept is learned
                    # If learned, prefer if a successor to the concept the previous question batch was on
                    valid_successors: List[str] = [
                        c_id
                        for c_id, prereqs in QUESTIONS_PREREQUISITE_DICT.items()
                        if prev_concept_id in prereqs and c_id in valid_current_concepts
                    ]

                    if len(valid_successors) > 1:
                        # [2.2] If multiple successors, pick between them
                        print("2.2 Multiple successors found")
                        return use_link_clicks_or_random(map_uuid, user_id, valid_successors)

                # [2.3] If not valid and not learned (with valid successors), see if we can get the
                # last question batch completed on a valid concept and use that!
                prev_qs_on_valid_cs = prev_question_batches.filter(
                    concept__cytoscape_id__in=valid_current_concepts
                )
                if prev_qs_on_valid_cs.count() > 0:
                    print("2.3 Concept from completed prev batch is valid")
                    return Response(
                        {
                            "concept_id": prev_qs_on_valid_cs.latest(
                                "time_started"
                            ).concept.cytoscape_id
                        },
                        status=status.HTTP_200_OK,
                    )

            # [3.0] If all else fails, pick from valid current concepts
            print("3.0 Picking from valid concepts")
            return use_link_clicks_or_random(map_uuid, user_id, valid_current_concepts)

            # Display an error if something goes wrong.
        except Exception as e:
            print("ERROR: ", e)
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


def get_valid_current_concept_ids(user_id: str, map_uuid: str) -> List[str]:
    """Get concept ids of concepts which are potential current concepts for the user.

    This means they are both on the path to one of their goals and all prerequisites are set as
    learned.
    """
    concept_ids = list(QUESTIONS_PREREQUISITE_DICT)
    # [2.1] Towards their goal
    goals_model = GoalModel.get(user_id, map_uuid)
    goals = goals_model.goal_concepts if goals_model else {}
    is_towards_goal = [
        any(
            concept_id in QUESTIONS_PREREQUISITE_DICT[goal_id] or concept_id == goal_id
            for goal_id in goals
        )
        for concept_id in concept_ids
    ]

    # [2.2] Check all concept's prerequisites are learned and it's not learned
    learned_model = LearnedModel.get(user_id, map_uuid)
    learned_concepts = learned_model.learned_concepts if learned_model else {}
    are_all_prereqs_learned = [
        # All prereqs must be learned!
        all(
            learned_concepts.get(prereq, False)
            for prereq in QUESTIONS_PREREQUISITE_DICT[concept_id]
        )
        and not learned_concepts.get(concept_id, False)  # Can't already be learned!
        for concept_id in concept_ids
    ]
    return [
        concept_id
        for count, concept_id in enumerate(concept_ids)
        if are_all_prereqs_learned[count] and is_towards_goal[count]
    ]


def use_link_clicks_or_random(map_uuid: str, user_id: str, possible_concept_ids: List[str]):
    """From `possible_concept_ids`, pick the concept which has had a content link click clicked on
    it most recently if any have ever been clicked.

    Otherwise, pick randomly!
    """
    if len(possible_concept_ids) == 1:
        # Only 1 valid option. Pick this
        return Response(
            {"concept_id": possible_concept_ids[0]},
            status=status.HTTP_200_OK,
        )
    relevant_link_clicks = LinkClickModel.objects.filter(
        map=map_uuid, user_id=user_id, concept_id__in=possible_concept_ids
    )
    return Response(
        {
            "concept_id": relevant_link_clicks.latest("timestamp").concept_id
            if relevant_link_clicks.exists()
            else random.choice(possible_concept_ids)
        },
        status=status.HTTP_200_OK,
    )
