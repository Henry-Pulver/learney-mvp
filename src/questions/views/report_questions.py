from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

import boto3
from botocore.exceptions import ClientError
from learney_web.settings import IS_PROD
from questions.models import QuestionTemplate
from questions.utils import uuid_and_params_from_frontend_id

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
        template_id, params = uuid_and_params_from_frontend_id(request.data["question"]["id"])
        question_template = QuestionTemplate.objects.get(id=template_id).prefetch_related("concept")
        concept_name = question_template.concept.name

        # Deactivate question template!
        question_template.active = False
        question_template.save()

        subject = f"Question broken on '{concept_name}'"

        admin_edit_link = get_admin_edit_link(str(template_id))
        # The email body for recipients with non-HTML email clients.
        body_text = (
            f"Question on {concept_name} reported as broken!\r\n"
            f"Params used: {params}\r\n"
            f"Issue type: {request.data['type']}\r\n"
            f"Message: \n{request.data['message']}\r\n"
            f"Link to edit: {admin_edit_link}"
        )

        # The HTML body of the email.
        body_html = f"""<html>
        <head></head>
        <body>
          <h1>Question on {concept_name} reported as broken!</h1>
          <br/>
          <p>
          Issue type: {request.data['type']}
          <br/>
          Params used: {params}\r\n
          <br/>
          Message: \n{request.data['message']}
          <br/>
            <a href='{admin_edit_link}'>Here is the link to edit the question</a>.
          </p>
        </body>
        </html>
        """

        client = boto3.client("ses", region_name="us-west-2")
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
