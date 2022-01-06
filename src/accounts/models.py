from django.db import models

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

    picture = models.URLField()
    locale = models.CharField(blank=True, max_length=8)
