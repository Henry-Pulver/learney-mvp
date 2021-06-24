from random import choice
from typing import Optional

from question_bot.utils import AnswerOutcome

FOUNDER_SLACK_IDS = ["U020USVD03D", "U0210S1DF60"]


class Messages:
    @staticmethod
    def signup(firstname: str) -> str:
        return (
            f"Hello {firstname}! :wave:\n\n"
            "*Congratulations* for signing up for the *Learney 0.1.0 Trial*! :tada:\n\n"
            "You smart. You wise. :brain:\n\n"
            "*How it works:* every day I'll send you questions on this Slack channel *personalised, given your goals"
            " and knowledge set in the Knowledge Map* :world_map:\n\n"
            "Just checking you have everything set up... :thinking_face:"
        )

    @classmethod
    def already_signed_up(cls) -> str:
        """Send when someone signs up on the GForm but they've already signed up!"""
        return (
            "Hi, you've already signed up, so no need to sign up to the "
            f"Learney 0.1.0 Trial again!\n\n {cls._reach_out()}"
        )

    @classmethod
    def not_on_learney(cls, relative_time_str: str) -> str:
        return (
            "Oh no! It seems you haven't made an account on the Learney platform yet!\n\n"
            "*Create an account here using the same email you used to sign up to Slack:* "
            ":point_right: https://app.learney.me/dashboard :point_left: and *set your learning goals* "
            f":goal_net: and *what you know* to receive your questions at {relative_time_str}.\n\n {cls._reach_out()}"
        )

    @staticmethod
    def no_goals() -> str:
        return (
            "Last thing! I promise! :pray:\n\n"
            "All you need to do is set a goal on Learney! :goal_net:\n\n"
            "Click a concept on the interactive Knowledge Map and click *Set Goal*\n\n"
            ":point_right: https://app.learney.me/dashboard :point_left:"
        )

    @classmethod
    def signup_complete(cls, relative_time_str: str, num_questions: int = 5) -> str:
        return (
            "That's it! :smile:\n\nSignup complete! :tada:\n\n"
            f"Your first set of {num_questions} questions will be sent here the "
            f"next time the clock strikes {relative_time_str}!\n\n {cls._reach_out()}"
        )

    @staticmethod
    def _reach_out() -> str:
        return (
            f"Reach out to <@{FOUNDER_SLACK_IDS[0]}> or <@{FOUNDER_SLACK_IDS[1]}> if you have any problems "
            f"or to suggest any improvements! :raised_hands:"
        )

    @staticmethod
    def unknown_channel_message() -> str:
        return (
            "Not sure what you mean! :thinking_face:\n\n"
            "If you're answering a question, please do so in the thread of the question! :smile:"
        )

    @staticmethod
    def no_questions() -> str:
        return "We're out of questions for you! :cry:\n\nReally sorry!"

    @staticmethod
    def question_start(concept_name: str) -> str:
        return (
            "It's time for your questions! :tada:\n\n"
            f"Today your questions are focused on *{concept_name}*\n\n"
            "Please answer in the comment thread of the question! :smile:\n\n"
            f"Answer *Pass* if you get stuck and want to find out the answer! :smile:"
        )

    @staticmethod
    def question_end(num_questions: int = 5) -> str:
        return (
            "Answer them by this time tomorrow for your next set of questions! :smile:\n\n"
            "If these questions aren't right for you, send *Too Hard*, *Too Easy* or *Bored* in chat "
            f"to get a new set of {num_questions} questions better suited to you."
        )

    @staticmethod
    def question_already_answered() -> str:
        return "Question already answered! :smile:"

    @staticmethod
    def answer_thread() -> str:
        return "Answer here! :point_down:"

    POTENTIAL_NO_ANSWERS_ONE_LINER = [
        "Don't worry! We all have busy days sometimes :smile:",
        "Don't sweat it! :sweat:",
        "That's no problem! But today is going to be different... right? :crossed_fingers:",
        "Today is going to be different! Right? :muscle:",
    ]

    @classmethod
    def no_answers_received(cls, num_questions: int = 5) -> str:
        return (
            "Uh-oh! We didn't receive your answers. :disappointed:\n\n"
            f"{choice(cls.POTENTIAL_NO_ANSWERS_ONE_LINER)}\n\n"
            "Was it because they were the wrong difficulty? :thinking_face:\n\n"
            f"If so, send *Too Hard*, *Too Easy* or *Bored* to get a new set of {num_questions} "
            f"questions. :question:\n\n"
            f"Otherwise, answer the previous questions we sent and we'll send you {num_questions} "
            f"more this time tomorrow! :alarm_clock:"
        )

    @staticmethod
    def correct_incorrect_message(correct: AnswerOutcome, correct_answer: str) -> str:
        if correct == AnswerOutcome.correct:
            return "That's correct! :white_check_mark: :tada:"
        elif correct == AnswerOutcome.incorrect:
            return (
                "Afraid that's not quite right :x:\n\n" f"The correct answer is: {correct_answer}"
            )
        elif correct == AnswerOutcome.passed:
            return f"Sure! The correct answer is: {correct_answer}"
        else:
            return (
                "Hmm, not totally sure what you meant there. :thinking_face:\n\n"
                "Try again! Check the answer is the right format :smile:"
            )

    @staticmethod
    def end_of_pilot() -> str:
        return (
            "That's it for this week of questions! We hope you found it useful! *Thank you so much* for taking part! :pray:\n\n"
            f"If you'd like to extend this week further, reach out to <@{FOUNDER_SLACK_IDS[0]}> or <@{FOUNDER_SLACK_IDS[1]}>! :smile:\n\n"
            f"We would *love to hear your thoughts* on the question-answer through Slack in a quick call - "
            "pick a slot that suits you on here:\nhttps://calendly.com/mgphillips/30min\n"
            "Or here:\nhttps://calendly.com/henrypulver/learney"
        )

    @staticmethod
    def too_easy() -> str:
        return (
            "Message received, loud and clear! :speaker:\n\n"
            "We'll send you more questions now - if they aren't hard enough, try updating the"
            " Knowledge Map (here: https://app.learney.me/dashboard) and setting another concept"
            " as known so you get harder questions :smile:"
        )

    @staticmethod
    def too_hard() -> str:
        return (
            "Message received, loud and clear! :speaker:\n\n"
            "We'll send you more questions now - if they are still too difficult, try updating the"
            " Knowledge Map (here: https://app.learney.me/dashboard) and remove another concept as known so you "
            "get questions on slightly easier concepts :smile:"
        )

    @staticmethod
    def bored() -> str:
        return (
            "Message received, loud and clear! :speaker:\n\n"
            "We'll send you more questions now - I hope they're less boring than the previous questions! :crossed_fingers:"
        )

    @staticmethod
    def run_out_of_questions(concept_name: str) -> str:
        return f"We've run out of questions for *{concept_name}*"
