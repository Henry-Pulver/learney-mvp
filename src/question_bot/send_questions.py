import random
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from typing import List

import numpy as np
from slack_sdk import WebClient as SlackWebClient

from goals.models import GoalModel
from knowledge_maps.orig_map_uuid import ORIG_MAP_UUID
from learned.models import LearnedModel
from learney_web import settings
from notion_client import Client as NotionClient
from question_bot.models import AnswerModel, QuestionLastAskedModel, SlackBotUserModel
from question_bot.questions import Question
from question_bot.slack_message_text import FOUNDER_SLACK_IDS, Messages
from question_bot.utils import MapStatus, email_to_user_id, get_concepts_asked_about

CONCEPTS_NOTION_DB_ID = "e35066c7-0117-4c82-bb21-4ce579db798a"
INITIAL_TRIAL_LENGTH = 7  # days

QUESTION_NUMBER_EMOJIS = [":one:", ":two:", ":three:", ":four:", ":five:"]


def get_days_until_end(user: SlackBotUserModel, duration: int) -> int:
    return (user.active_since + timedelta(days=duration) - date.today()).days


def has_just_run(user_model: SlackBotUserModel) -> bool:
    prev_q_times = QuestionLastAskedModel.objects.filter(user_email=user_model.user_email)
    if prev_q_times.count() > 0:
        secs_since_send = (
            datetime.now(timezone.utc) - prev_q_times.latest("time_asked").time_asked
        ).total_seconds()
        QuestionLastAskedModel.objects.create(user_email=user_model.user_email)
        return secs_since_send < 120
    else:
        QuestionLastAskedModel.objects.create(user_email=user_model.user_email)
        return False


def send_questions(users_to_send_to: List[SlackBotUserModel], force: bool = False) -> None:
    """Sends questions all."""
    slack_client = SlackWebClient(settings.SLACK_TOKEN)
    notion_client = NotionClient(auth=settings.NOTION_KEY)

    for user_model in users_to_send_to:
        print(f"USER: {user_model.user_email}")
        user_id = email_to_user_id(user_model.user_email)
        # Check whether previous questions were answered
        all_questions_asked = AnswerModel.objects.filter(user_email=user_model.user_email)
        first_time = all_questions_asked.count() == 0
        if not first_time:
            ordered_questions = all_questions_asked.order_by("-time_asked")
            last_set_of_questions = ordered_questions[: user_model.num_questions_per_day]
        days_until_end = get_days_until_end(user_model, INITIAL_TRIAL_LENGTH)

        # If questions answered (or force, or first time) send a new batch
        if (
            first_time
            or force
            or len([None for question in last_set_of_questions if question.answered])
            >= user_model.num_questions_per_day - 1
        ):
            # Get the current state of this user's Knowledge Map(TM)
            user_goals = GoalModel.objects.filter(map_uuid=ORIG_MAP_UUID, user_id=user_id).latest(
                "last_updated"
            )
            if len(user_goals.goal_concepts) == 0:
                slack_client.chat_postMessage(
                    channel=user_model.slack_user_id,
                    text=Messages.no_goals(),
                )
                return
            user_learned_data = LearnedModel.objects.filter(map_uuid=ORIG_MAP_UUID, user_id=user_id)
            learned_concepts = (
                user_learned_data.latest("last_updated").learned_concepts
                if user_learned_data.count() > 0
                else {}
            )

            map_status = MapStatus(
                goal_dict=user_goals.goal_concepts,
                learned_dict=learned_concepts,
            )

            # Find the main concepts questions were asked about previously
            main_concept_asked_about = (
                get_concepts_asked_about(last_set_of_questions) if not first_time else []
            )

            # Build a list of the concepts to choose questions from, ordered based on priority
            ordered_concept_ids: List[str] = []

            if not force:  # if force, ignore previous questions
                # Pick out the main concept from those asked about previously
                for concept_id, count in main_concept_asked_about:
                    if concept_id in map_status.next_concepts:
                        ordered_concept_ids.append(concept_id)
                        break
            if len(ordered_concept_ids) == 0:
                ordered_concept_ids.append(random.choice(list(map_status.next_concepts)))

            # Add known immediate predecessors as revision in any order
            for concept_id in settings.ORIG_MAP_PREDECESSOR_DICT.get(ordered_concept_ids[0], set()):
                ordered_concept_ids.append(concept_id)
            # Add other next concepts + lastly other learned concepts
            for concept_id in list(map_status.next_concepts) + list(map_status.learned_concepts):
                if concept_id not in ordered_concept_ids:
                    ordered_concept_ids.append(concept_id)
            print(f"next concepts: {map_status.next_concepts}")
            print(
                f"ordered_concept_ids: {[settings.ORIG_MAP_CONCEPT_NAMES[c_id] for c_id in ordered_concept_ids]}"
            )

            if len(ordered_concept_ids) == 0:
                slack_client.chat_postMessage(
                    channel=user_model.slack_user_id,
                    text=Messages.no_questions(),
                )
                for founder_id in FOUNDER_SLACK_IDS:
                    slack_client.chat_postMessage(
                        channel=founder_id,
                        text=Messages.no_questions(),
                    )
                return

            # Get history of questions asked of this user
            all_concepts_asked_about = {
                concept_id: count
                for concept_id, count in get_concepts_asked_about(all_questions_asked)
            }
            question_ids_asked = [
                q_id["question_id"] for q_id in all_questions_asked.values("question_id")
            ]

            # Choose which concepts each question will come from
            question_concepts_chosen: List[str] = []
            while (
                len(question_concepts_chosen) < user_model.num_questions_per_day
                and len(ordered_concept_ids) > 0
            ):
                chosen_concept = ordered_concept_ids[0]
                print(f"Concept: {settings.ORIG_MAP_CONCEPT_NAMES[chosen_concept]}")
                notion_response = notion_client.databases.query(
                    database_id=CONCEPTS_NOTION_DB_ID,
                    filter={"property": "ID", "text": {"equals": chosen_concept}},
                )
                if len(notion_response["results"]) > 0:
                    total_num_concept_qs = int(
                        notion_response["results"][0]["properties"]["n(questions)"]["number"]
                    )
                else:
                    total_num_concept_qs = 0
                num_qs_to_add = user_model.num_questions_per_day - len(question_concepts_chosen)
                print(f"Number of questions remaining to send: {num_qs_to_add}")
                print(f"Total number of questions for this concept: {total_num_concept_qs}")
                print(
                    f"Number of questions previously asked about this concept: {all_concepts_asked_about.get(chosen_concept, 0)}"
                )

                if all_concepts_asked_about.get(chosen_concept, 0) < total_num_concept_qs:
                    num_qs_for_concept_to_add = total_num_concept_qs - all_concepts_asked_about.get(
                        chosen_concept, 0
                    )
                    print(
                        f"Number of questions to add for this concept: {num_qs_for_concept_to_add}"
                    )
                    if num_qs_for_concept_to_add <= num_qs_to_add:
                        del ordered_concept_ids[0]
                        for slack_id in FOUNDER_SLACK_IDS:
                            slack_client.chat_postMessage(
                                channel=slack_id,
                                text=Messages.run_out_of_questions(
                                    settings.ORIG_MAP_CONCEPT_NAMES[chosen_concept]
                                ),
                            )
                    for num_added in range(min(num_qs_for_concept_to_add, num_qs_to_add)):
                        question_concepts_chosen.append(chosen_concept)
                else:
                    del ordered_concept_ids[0]
                    for slack_id in FOUNDER_SLACK_IDS:
                        slack_client.chat_postMessage(
                            channel=slack_id,
                            text=Messages.run_out_of_questions(
                                settings.ORIG_MAP_CONCEPT_NAMES[chosen_concept]
                            ),
                        )

            question_concept_counter = Counter(question_concepts_chosen)
            chosen_questions = []
            for question_concept_id in question_concept_counter:
                # Get the questions that are possible choices
                notion_response = notion_client.databases.query(
                    database_id=CONCEPTS_NOTION_DB_ID,
                    filter={"property": "ID", "text": {"equals": question_concept_id}},
                )
                possible_questions = []
                for topic_block in notion_client.blocks.children.list(
                    block_id=notion_response["results"][0]["id"].replace("-", "")
                )["results"]:
                    if (
                        topic_block["type"] == "unsupported"
                    ):  # this block is the database of questions for this concept
                        # Decide which questions to ask
                        concept_question_page_list = notion_client.databases.query(
                            database_id=topic_block["id"]
                        )["results"]
                        for question_page in concept_question_page_list:
                            question = Question(
                                concept_id=question_concept_id,
                                question_page=question_page,
                            )
                            if question.question_id not in question_ids_asked:
                                question.get_text_from_question_blocks(
                                    notion_client.blocks.children.list(
                                        block_id=question_page["id"].replace("-", "")
                                    )["results"]
                                )
                                possible_questions.append(question)
                        chosen_questions += list(
                            np.random.choice(
                                possible_questions,
                                min(
                                    question_concept_counter[question_concept_id],
                                    len(possible_questions),
                                ),
                                replace=False,
                            )
                        )
                        break

            # Starting message
            for concept_id in question_concept_counter:
                slack_client.chat_postMessage(
                    channel=user_model.slack_user_id,
                    text=Messages.question_start(settings.ORIG_MAP_CONCEPT_NAMES[concept_id]),
                )
                break

            for question, emoji in zip(
                chosen_questions, QUESTION_NUMBER_EMOJIS
            ):  # Send questions to Slack
                if question.question_text:
                    slack_response = slack_client.chat_postMessage(
                        channel=user_model.slack_user_id,
                        text=f"{emoji} {question.question_text}",
                    )
                    slack_client.chat_postMessage(
                        channel=user_model.slack_user_id,
                        thread_ts=slack_response["ts"],
                        text=Messages.answer_thread(),
                    )
                    AnswerModel.objects.create(
                        user_email=user_model.user_email,
                        question_id=question.question_id,
                        question_type=question.question_type,
                        answer_type=question.answer_type,
                        correct_answer=question.correct_answer,
                        feedback=question.feedback,
                        time_asked=slack_response["ts"],
                        time_answered=None,
                    )

            # End message
            slack_client.chat_postMessage(
                channel=user_model.slack_user_id,
                text=Messages.question_end(
                    relative_time_str=user_model.relative_question_time,
                    days_until_end_of_trial=days_until_end,
                    paid=user_model.paid,
                    num_questions=user_model.num_questions_per_day,
                ),
            )
        else:  # Previous day's questions not answered
            slack_client.chat_postMessage(
                channel=user_model.slack_user_id,
                text=Messages.no_answers_received(
                    days_until_end_of_trial=days_until_end,
                    paid=user_model.paid,
                    num_questions=user_model.num_questions_per_day,
                ),
            )
        if (
            20
            <= AnswerModel.objects.filter(answered=True, user_email=user_model.user_email).count()
            < 25
        ):
            slack_client.chat_postMessage(
                channel=user_model.slack_user_id, text=Messages.twenty_questions_answered()
            )
            for founder_id in FOUNDER_SLACK_IDS:
                slack_client.chat_postMessage(
                    channel=founder_id,
                    text=Messages.twenty_questions_founders(user_model.slack_user_id),
                )
