from django.core.cache import cache
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from questions.models import QuestionTemplate
from questions.template_parser import ParsingError


class QuestionTemplateView(APIView):
    def get(self, request: Request, format=None) -> Response:
        template_data = QuestionTemplate.objects.values().get(id=request.GET["template_id"])
        return Response(template_data, status=status.HTTP_200_OK)

    def post(self, request: Request, format=None) -> Response:
        template_id = request.data["template_id"]
        template_data = request.data["template"]

        # This caching makes this view lightning fast!
        template = cache.get(f"template_{template_id}")
        if template is None:
            template = QuestionTemplate.objects.get(id=template_id)
            cache.set(f"template_{template_id}", template, timeout=60)

        template.template_text = template_data["template_text"]
        template.difficulty = template_data["difficulty"]
        template.title = template_data["title"]
        template.active = template_data["active"]
        template.correct_answer_letter = template_data["correct_answer_letter"]
        try:
            if request.data["save"]:
                template.save()
            response = template.to_question_json()
            return Response(response, status=status.HTTP_200_OK)
        except ParsingError as error:
            return Response(
                {
                    "title": template.title,
                    "template_id": template.id,
                    "question_text": "",
                    "question_type": "",
                    "answers_order_randomised": ["", "", "", ""],
                    "correct_answer": "",
                    "feedback": "",
                    "difficulty": template.difficulty,
                    "params": {},
                    "error": str(error),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
