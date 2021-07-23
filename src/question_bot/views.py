import logging
from datetime import date, datetime

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from slack_sdk import WebClient

from goals.models import GoalModel
from learney_web import settings
from page_visits.models import PageVisitModel
from question_bot.models import AnswerModel, SlackBotUserModel
from question_bot.process_slack_messages import DifficultyChange, string_to_difficulty
from question_bot.send_questions import get_days_until_end, has_just_run, send_questions
from question_bot.serializers import SlackBotUserSerializer
from question_bot.slack_message_text import Messages
from question_bot.utils import (
    AnswerOutcome,
    check_answer,
    get_first_name,
    get_nearest_half_hour,
    get_utc_time_to_send,
    is_on_learney,
)


def deactivate_user(user: SlackBotUserModel):
    user.active = False
    user.active_since = None
    user.save()
    WebClient(settings.SLACK_TOKEN).chat_postMessage(
        channel=user.slack_user_id,
        text=Messages.end_of_trial(),
    )


class QuestionUserView(APIView):
    def post(self, request: Request, format=None) -> Response:
        print("FORM SUBMITTED")
        print(f"request.data: {request.POST}")

        user_email = request.POST["email"]
        slack_client = WebClient(settings.SLACK_TOKEN)

        # Check this person hasn't already signed up!
        try:
            user = SlackBotUserModel.objects.get(user_id=user_email)
            slack_client.chat_postMessage(
                channel=user.slack_user_id, text=Messages.already_signed_up()
            )
            return Response(
                f"User with email {user_email} already exists",
                status=status.HTTP_200_OK,
            )
        except ObjectDoesNotExist:
            print("NO EXISTING DB ENTRY")

        # Check if user is on Learney Slack
        try:
            slack_response = slack_client.users_lookupByEmail(email=user_email)
        except Exception:
            print("EXCEPTION HIT - NOT ON SLACK")
            slack_response = {"ok": False}
        print(slack_response)
        on_slack = slack_response["ok"]
        slack_user_id = slack_response["user"]["id"] if on_slack else ""

        if on_slack:
            print("ON SLACK")
            slack_client.chat_postMessage(
                channel=slack_user_id,
                text=Messages.signup(get_first_name(slack_response)),
            )

        # Check if user is signed up to learney
        on_learney = is_on_learney(user_email)
        if on_learney:
            print("On Learney!")
            goals_set = GoalModel.objects.filter(user_id=user_email).count() > 0
            if not goals_set:
                slack_client.chat_postMessage(
                    channel=slack_user_id,
                    text=Messages.no_goals(),
                )
        else:
            print("Not on Learney!")
            goals_set = False
            if on_slack:
                # send message through Slack telling them to make an account using their email!
                slack_client.chat_postMessage(
                    channel=slack_user_id,
                    text=Messages.not_on_learney(
                        request.data["relative_time_to_receive_questions"]
                    ),
                )
        if on_slack and on_learney and goals_set:
            slack_client.chat_postMessage(
                channel=slack_user_id,
                text=Messages.signup_complete(request.data["relative_time_to_receive_questions"]),
            )

        # Make an entry!
        serializer = SlackBotUserSerializer(
            data=dict(
                user_id=user_email,
                relative_question_time=request.data["relative_time_to_receive_questions"],
                timezone=request.data["timezone"],
                utc_time_to_send=get_utc_time_to_send(
                    request.data["relative_time_to_receive_questions"],
                    request.data["timezone"],
                ),
                on_slack=on_slack,
                slack_user_id=slack_user_id,
                on_learney=on_learney,
                goal_set=goals_set,
                active=on_slack and on_learney and goals_set,
                active_since=date.today() if on_slack and on_learney and goals_set else None,
                paid=False,
            )
        )
        if serializer.is_valid():
            serializer.save()
            user = SlackBotUserModel.objects.get(user_id=user_email)
            if has_just_run(user):
                print(f"{user.user_id} HAS JUST RECEIVED QUESTIONS - CANCELLING")
                logging.debug(f"{user.user_id} HAS JUST RECEIVED QUESTIONS - CANCELLING")
            else:
                logging.debug(f"Sending to {user.user_id}")
                send_questions([user])
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request: Request, format=None) -> Response:
        user_email = request.data["email"]
        print(f"UPDATING DB ENTRY FOR {user_email}")

        # Check this person has already signed up
        try:
            user = SlackBotUserModel.objects.get(user_id=user_email)
            print("DB ENTRY EXISTS!")
            slack_client = WebClient(settings.SLACK_TOKEN)
            if user.on_learney:
                print("On Learney!")
                if not user.goal_set:
                    goal_set = GoalModel.objects.filter(user_id=user_email).count() > 0
                    print("Goal now set!")
                    if goal_set:
                        if user.on_slack:
                            slack_client.chat_postMessage(
                                channel=user.slack_user_id,
                                text=Messages.signup_complete(user.relative_question_time),
                            )
                            if has_just_run(user):
                                print(f"{user.user_id} HAS JUST RECEIVED QUESTIONS - CANCELLING")
                                logging.debug(
                                    f"{user.user_id} HAS JUST RECEIVED QUESTIONS - CANCELLING"
                                )
                            else:
                                logging.debug(f"Sending to {user.user_id}")
                                send_questions([user])
                        user.goal_set = True
                        user.active = user.on_slack
                        user.active_since = date.today() if user.on_slack else None
                        user.save()
                return Response(
                    f"Q&A user with email {user_email} already exists",
                    status=status.HTTP_200_OK,
                )
            else:
                print("Not on learney!")
                user.on_learney = True
                user.save()
                slack_client.chat_postMessage(channel=user.slack_user_id, text=Messages.no_goals())
                return Response(
                    f"Q&A user with email {user_email} updated",
                    status=status.HTTP_200_OK,
                )
        except ObjectDoesNotExist:
            print("NO DB ENTRY")
            return Response(
                f"No Q&A user with email {user_email}",
                status=status.HTTP_304_NOT_MODIFIED,
            )

    def delete(self, request: Request, format=None) -> Response:
        user_id = request.data["email"]
        SlackBotUserModel.objects.filter(user_id=user_id).delete()
        return Response(
            f"Entry with user_email={user_id} deleted",
            status=status.HTTP_204_NO_CONTENT,
        )


class QuestionsView(APIView):
    def get(self, request: Request, format=None) -> Response:
        print("QUESTIONS GET RECEIVED")
        # Work out who to send questions to at this time
        nearest_half_hour = get_nearest_half_hour(datetime.utcnow().time())
        users_to_maybe_send_to = SlackBotUserModel.objects.filter(
            utc_time_to_send=nearest_half_hour, active=True
        )

        users_to_send_to = []
        for user in users_to_maybe_send_to:
            # Check it hasn't just run (hack to block multiple requests causing problems)
            if has_just_run(user):
                print(f"{user.user_id} HAS JUST RECEIVED QUESTIONS - CANCELLING")
                logging.debug(f"{user.user_id} HAS JUST RECEIVED QUESTIONS - CANCELLING")
            else:
                logging.debug(f"{user.user_id} A USER TO SEND TO")
                # Should this user still be active?
                if get_days_until_end(user, 7) <= 0 and not user.paid:
                    deactivate_user(user)
                else:
                    users_to_send_to.append(user)
        logging.debug(f"Sending to {len(users_to_send_to)} users")

        send_questions(users_to_send_to)

        users_yet_to_activate = SlackBotUserModel.objects.filter(
            utc_time_to_send=nearest_half_hour, active=False
        )

        for user in users_yet_to_activate:
            if (date.today() - user.active_since).days >= 2 and not has_just_run(user):
                WebClient(settings.SLACK_TOKEN).chat_postMessage(
                    channel=user.user_id,
                    text=Messages.dont_forget_to_activate((date.today() - user.active_since).days),
                )
        return Response(
            f"Questions sent to {len(users_to_send_to)} users", status=status.HTTP_200_OK
        )


class FeedbackView(APIView):
    def post(self, request: Request, format=None) -> Response:
        print("POST RECEIVED!")

        # Requirement of Slack Events API to verify URL
        if request.data.get("type") == "url_verification":
            print("CHALLENGE ACCEPTED!")
            return Response(request.data["challenge"], status=status.HTTP_200_OK)

        # This view should only be hit by events. If it's not an event, don't go near it
        if "event" not in request.data:
            return Response("Computer says no", status=status.HTTP_400_BAD_REQUEST)

        event_data = request.data["event"]
        if "bot_id" in event_data or "bot_id" in event_data.get("message", {}):
            print("BOT")
            return Response("Message sent by the bot!", status=status.HTTP_200_OK)

        print(f"request data: {request.data}")
        slack_client = WebClient(settings.SLACK_TOKEN)
        # TODO: Change this - Slack Events API can only have 1 endpoint, so this is the only endpoint used.
        #  Thus we have to handle both responses to questions and Slack signups here!
        if event_data["type"] == "team_join":
            print(f'NEW MEMBER WITH EMAIL {event_data["user"]["profile"]["email"]} JOINED')
            try:
                user_model = SlackBotUserModel.objects.get(
                    user_id=event_data["user"]["profile"]["email"]
                )
                print("SLACK USER DB EXISTS")
                # if no ObjectDoesNotExist error, we should update the entry
                user_model.slack_user_id = event_data["user"]["id"]
                user_model.on_slack = True
                user_model.active = user_model.on_learney and user_model.goal_set
                user_model.active_since = (
                    date.today() if user_model.on_learney and user_model.goal_set else None
                )
                user_model.save()

                slack_client.chat_postMessage(
                    channel=user_model.slack_user_id,
                    text=Messages.signup(get_first_name(event_data)),
                )
                on_learney = (
                    PageVisitModel.objects.filter(
                        user_id=event_data["user"]["profile"]["email"]
                    ).count()
                    > 0
                )
                if not on_learney:
                    print("NOT ON LEARNEY")
                    # send message through Slack telling them to make an account using their email!
                    slack_client.chat_postMessage(
                        channel=user_model.slack_user_id,
                        text=Messages.not_on_learney(user_model.relative_question_time),
                    )
                else:
                    slack_client.chat_postMessage(
                        channel=user_model.slack_user_id,
                        text=Messages.signup_complete(user_model.relative_question_time),
                    )
                    if has_just_run(user_model):
                        print(f"{user_model.user_id} HAS JUST RECEIVED QUESTIONS - CANCELLING")
                        logging.debug(
                            f"{user_model.user_id} HAS JUST RECEIVED QUESTIONS - CANCELLING"
                        )
                    else:
                        logging.debug(f"Sending to {user_model.user_id}")
                        send_questions([user_model])
            except ObjectDoesNotExist:
                print(f'NO SLACK USER WITH EMAIL {event_data["user"]["profile"]["email"]} EXISTS')
            return Response("User joined Slack", status=status.HTTP_200_OK)
        # The actual feedback code starts here :)
        elif event_data["type"] == "message":
            print("MESSAGE!")

            if "thread_ts" in event_data:  # It's a reply
                time_asked = event_data["thread_ts"]
                question_model = AnswerModel.objects.get(time_asked=time_asked)
                if not question_model.answered:
                    answer_given = event_data["text"]

                    correct = check_answer(
                        answer_type=question_model.answer_type,
                        answer_given=answer_given,
                        correct_answer=question_model.correct_answer,
                        allow_again=question_model.answer_given
                        == "",  # after 1st try, this won't be true
                    )

                    # FEEDBACK - Correct/incorrect?
                    slack_client.chat_postMessage(
                        channel=event_data["user"],
                        thread_ts=event_data["thread_ts"],
                        text=Messages.correct_incorrect_message(
                            correct, question_model.correct_answer
                        ),
                    )
                    if (
                        correct in [AnswerOutcome.incorrect, AnswerOutcome.passed]
                        and question_model.feedback
                    ):  # Give feedback
                        print("GIVING FEEDBACK")
                        slack_client.chat_postMessage(
                            channel=event_data["user"],
                            thread_ts=time_asked,
                            text=question_model.feedback,
                        )

                    if correct == AnswerOutcome.try_again:
                        print("HAVE ANOTHER GO")
                        question_model.answer_given = answer_given
                        question_model.save()
                    else:
                        # update DB entry
                        question_model.answered = True
                        question_model.answer_given = answer_given
                        question_model.correct = correct == AnswerOutcome.correct
                        question_model.time_answered = datetime.now()
                        question_model.save()
                    return Response("Feedback given", status=status.HTTP_200_OK)
                else:
                    slack_client.chat_postMessage(
                        channel=event_data["user"],
                        thread_ts=time_asked,
                        text=Messages.question_already_answered(),
                    )
                    return Response("Question already answered", status=status.HTTP_200_OK)

            else:  # Not a reply - is a message in chat!
                print(f"EVENT DATA: {event_data}")
                difficulty = string_to_difficulty(event_data.get("text", ""))
                if difficulty is not None:
                    # reply then send more questions
                    user_id = event_data.get("user", event_data.get("message", {}).get("user"))
                    diff_to_message = {
                        DifficultyChange.too_easy: Messages.too_easy(),
                        DifficultyChange.bored: Messages.bored(),
                        DifficultyChange.too_hard: Messages.too_hard(),
                    }
                    # Check not already running
                    # TODO: Fix this hack
                    if has_just_run(SlackBotUserModel.objects.get(slack_user_id=user_id)):
                        print("JUST RUN - CANCELLING")
                        return Response("Message, but not a reply", status=status.HTTP_200_OK)
                    slack_client.chat_postMessage(channel=user_id, text=diff_to_message[difficulty])
                    send_questions(SlackBotUserModel.objects.filter(slack_user_id=user_id), True)
                else:  # unknown message - tell em they're off their rocker
                    slack_client.chat_postMessage(
                        channel=event_data.get("user", event_data.get("message", {}).get("user")),
                        text=Messages.unknown_channel_message(),
                    )
                return Response("Message, but not a reply", status=status.HTTP_200_OK)
        else:
            return Response("Event not supported!", status=status.HTTP_400_BAD_REQUEST)
