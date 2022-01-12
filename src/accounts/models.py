from django.db import models

from learney_backend.models import ContentLinkPreview, ContentVote

# email: "henrypulver13@gmail.com"
# email_verified: true
# family_name: "Pulver"
# given_name: "Henry"
# locale: "en-GB"
# name: "Henry Pulver"
# nickname: "henrypulver13"
# picture: "https://lh3.googleusercontent.com/a-/AOh14Gg82_yj2aTeve54l0gbNNaZTCtrbqwE3UFhi_NpDw=s96-c"
# sub: "google-oauth2|107422942042952650102"
# updated_at: "2022-01-05T14:50:01.592Z"


class User(models.Model):
    id = models.CharField(primary_key=True, max_length=255)

    name = models.CharField(max_length=255)
    nickname = models.CharField(blank=True, max_length=255)
    given_name = models.CharField(blank=True, max_length=255)
    family_name = models.CharField(blank=True, max_length=255)

    picture = models.URLField(max_length=1000)
    locale = models.CharField(blank=True, max_length=8)

    checked_content_links = models.ManyToManyField(
        ContentLinkPreview,
        related_name="checked_by",
        help_text="The content links that this user has checked",
    )
