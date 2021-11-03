from django.test import TestCase

from questions.serializers import QuestionSerializer


class QuestionSerializerTests(TestCase):
    TEST_QUESTION_TEXT = "This is a box.\n\nA WHAT?!?"
    TEST_ANSWER_TEXT = ["A box", "Not a box?", "A lemon", "Turnip"]
    TEST_FEEDBACK_TEXT = "Oh, a box."
    TEST_AUTHOR_USER_ID = "learney|103489723y596810987"
    TEST_SESSION_ID = "13498674w59872rw34"

    def test_failed_set_up__empty_question(self):
        assert not QuestionSerializer(
            data=dict(
                question_text="",
                answer_text=self.TEST_ANSWER_TEXT,
                feedback_text=self.TEST_FEEDBACK_TEXT,
                author_user_id=self.TEST_AUTHOR_USER_ID,
                session_id=self.TEST_SESSION_ID,
            )
        ).is_valid()

    def test_failed_set_up__empty_answer(self):
        assert not QuestionSerializer(
            data=dict(
                question_text=self.TEST_QUESTION_TEXT,
                answer_text="",
                feedback_text=self.TEST_FEEDBACK_TEXT,
                author_user_id=self.TEST_AUTHOR_USER_ID,
                session_id=self.TEST_SESSION_ID,
            )
        ).is_valid()

    def test_failed_set_up__empty_feedback(self):
        assert not QuestionSerializer(
            data=dict(
                question_text=self.TEST_QUESTION_TEXT,
                answer_text=self.TEST_ANSWER_TEXT,
                feedback_text="",
                author_user_id=self.TEST_AUTHOR_USER_ID,
                session_id=self.TEST_SESSION_ID,
            )
        ).is_valid()

    def test_failed_set_up__string_answers(self):
        assert not QuestionSerializer(
            data=dict(
                question_text=self.TEST_QUESTION_TEXT,
                answer_text=str(self.TEST_ANSWER_TEXT),
                feedback_text=self.TEST_FEEDBACK_TEXT,
                author_user_id=self.TEST_AUTHOR_USER_ID,
                session_id=self.TEST_SESSION_ID,
            )
        ).is_valid()
