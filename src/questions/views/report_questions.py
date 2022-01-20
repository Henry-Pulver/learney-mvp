from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

import boto3
from botocore.exceptions import ClientError
from learney_web.settings import IS_PROD

CHARSET = "UTF-8"

# This address is verified with Amazon SES.
SENDER = "Question Problem Report <report-bot@learney.me>"
# TODO: change this
RECIPIENTS = ["henry@learney.me", "matthew@learney.me"]


def get_admin_edit_link(question_template_id: str) -> str:
    """Gets a link to the admin page to edit this question."""
    # TODO: Change this URL
    return f"https://{IS_PROD if '' else 'staging-'}api.learney.me/admin/<EDIT ME>/<EDIT THIS>/{question_template_id}/change/"


class ReportBrokenQuestionView(APIView):
    def post(self, request: Request, format=None) -> Response:
        # TODO: When new models are all sorted, change this!
        subject = f"Question broken report: {'TODO'}"

        # The email body for recipients with non-HTML email clients.
        body_text = "Amazon SES Test (Python)\r\n" "Question on {} reported as broken!"
        admin_edit_link = get_admin_edit_link("TODO")

        # The HTML body of the email.
        body_html = f"""<html>
        <head></head>
        <body>
          <h1>Question on {"TODO"} reported as broken!</h1>
          <p>
          <br/>
            <a href='{admin_edit_link}'>Here is the link to edit the question</a>.
          </p>
        </body>
        </html>
        """

        # Link to question
        # Contents of their message

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
