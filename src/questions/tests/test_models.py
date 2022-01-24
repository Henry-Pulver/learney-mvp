from datetime import time
from uuid import uuid4

import pytest
from django.test import TestCase

from questions.models import QuestionResponseModel, QuestionTemplate


class QuestionModelTests(TestCase):
    TEST_QUESTION_TEXT = "This is a box.\n\nA WHAT?!?"
    TEST_ANSWER_TEXT = ["A box", "Not a box?", "A lemon", "Turnip"]
    TEST_FEEDBACK_TEXT = "Oh, a box."
    TEST_AUTHOR_USER_ID = "learney|103489723y596810987"
    TEST_SESSION_ID = "13498674w59872rw34"

    @pytest.fixture(scope="class", autouse=True)
    def set_up(self):
        created_object = QuestionTemplate.objects.create(
            question_text=self.TEST_QUESTION_TEXT,
            answer_text=self.TEST_ANSWER_TEXT,
            feedback_text=self.TEST_FEEDBACK_TEXT,
            author_user_id=self.TEST_AUTHOR_USER_ID,
            session_id=self.TEST_SESSION_ID,
        )
        assert created_object
        self.id = created_object.id

    def test_get_from_db(self):
        question = QuestionTemplate.objects.get(id=self.id)
        assert question.question_text == self.TEST_QUESTION_TEXT
        assert question.answer_text == self.TEST_ANSWER_TEXT
        assert question.feedback_text == self.TEST_FEEDBACK_TEXT
        assert question.author_user_id == self.TEST_AUTHOR_USER_ID
        assert question.session_id == self.TEST_SESSION_ID


class QuestionResponseModelTests(TestCase):
    TEST_USER_ID = "learney|103489723y596810987"
    TEST_SESSION_ID = "31457834589769123253"
    TEST_QUESTION_ID = uuid4()
    TEST_RESPONSE = "A box"
    TEST_CORRECT = True
    TEST_TIME_TO_RESPOND = time(hour=0, minute=0, second=59, microsecond=420)

    @pytest.fixture(scope="class", autouse=True)
    def set_up(self):
        created_object = QuestionResponseModel.objects.create(
            user_id=self.TEST_USER_ID,
            session_id=self.TEST_SESSION_ID,
            question_id=self.TEST_QUESTION_ID,
            response=self.TEST_RESPONSE,
            correct=self.TEST_CORRECT,
            time_to_respond=self.TEST_TIME_TO_RESPOND,
        )
        assert created_object

    def test_get_from_db(self):
        question_answer = QuestionResponseModel.objects.get(
            user_id=self.TEST_USER_ID, question_id=self.TEST_QUESTION_ID
        )
        assert question_answer.user_id == self.TEST_USER_ID
        assert question_answer.session_id == self.TEST_SESSION_ID
        assert question_answer.question_id == self.TEST_QUESTION_ID
        assert question_answer.response == self.TEST_RESPONSE
        assert question_answer.correct == self.TEST_CORRECT
        assert question_answer.time_to_respond == self.TEST_TIME_TO_RESPOND
