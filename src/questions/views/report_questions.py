from django.core.cache import cache
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

import boto3
from botocore.exceptions import ClientError
from learney_web.settings import AWS_CREDENTIALS, IS_PROD
from questions.models import QuestionResponse, QuestionTemplate

CHARSET = "UTF-8"

# This address is verified with Amazon SES.
SENDER = "Question Problem Report <report-bot@learney.me>"
RECIPIENTS = ["henry@learney.me", "matthew@learney.me"]


def get_admin_edit_link(question_template_id: str) -> str:
    """Gets a link to the admin page to edit this question."""
    return (
        f"https://{IS_PROD if '' else 'staging-'}api.learney.me/admin/questions/questiontemplate/"
        f"{question_template_id}/change/"
    )


class ReportBrokenQuestionView(APIView):
    def post(self, request: Request, format=None) -> Response:
        template_id = request.data["question"]["template_id"]
        response_id = request.data["question"]["id"]

        question_template = QuestionTemplate.objects.prefetch_related("concept").get(id=template_id)
        concept_name = question_template.concept.name

        # Deactivate question template!
        question_template.active = False
        question_template.save()

        # Other views store novelty terms and the active question templates to pick from in cache,
        # so we need to invalidate these
        cache.delete(f"template_options_{question_template.concept.cytoscape_id}")
        cache.delete(
            f"novelty_terms_{QuestionResponse.objects.get(id=response_id).question_batch.id}"
        )

        subject = f"Question broken on '{concept_name}'"

        admin_edit_link = get_admin_edit_link(str(template_id))
        # The email body for recipients with non-HTML email clients.
        body_text = (
            f"Question on '{concept_name}' reported as broken!\r\n"
            f"Issue type: {request.data['type']}\r\n"
            f"User message: \n{request.data['message']}\r\n"
            f"Params used: {request.data['question']['params']}\r\n"
            f"Link to edit: {admin_edit_link}\r\n"
            f"Question_text: \n\n{request.data['question']['question_text']}"
        )

        # The HTML body of the email.
        body_html = f"""<html>
        <head></head>
        <body>
          <h1>Question on '{concept_name}' reported as broken!</h1>
          <p>
          <b>Issue type: {request.data['type']}</b>
          <br/>
          User message: \n{request.data['message']}
          <br/>
          Params used: {request.data['question']['params']}\r\n
          <br/>
            <a href='{admin_edit_link}'>Here is the link to edit the question</a>.
          <br/>
          Question_text: \n\n{request.data['question']['question_text']}
          </p>
        </body>
        </html>
        """

        client = boto3.client(
            "ses",
            region_name="us-west-2",
            aws_access_key_id=AWS_CREDENTIALS["ACCESS_ID"],
            aws_secret_access_key=AWS_CREDENTIALS["SECRET_KEY"],
        )
        try:
            # Provide the contents of the email.
            response = client.send_email(
                Destination={
                    "ToAddresses": RECIPIENTS,
                },
                Message={
                    "Body": {
                        "Html": {
                            "Charset": CHARSET,
                            "Data": body_html,
                        },
                        "Text": {
                            "Charset": CHARSET,
                            "Data": body_text,
                        },
                    },
                    "Subject": {
                        "Charset": CHARSET,
                        "Data": subject,
                    },
                },
                Source=SENDER,
            )
        # Display an error if something goes wrong.
        except ClientError as e:
            return Response(e.response["Error"]["Message"], status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                f"Email sent! Message ID: {response['MessageId']}", status=status.HTTP_200_OK
            )
