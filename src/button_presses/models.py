from django.db import models

ALL_BUTTONS = [
    ("log-in", " Log In"),
    ("log-out", "Log Out"),
    ("profile-image-button", "Profile Image"),
    ("make-suggestion", "Make Suggestion"),
    ("content-suggestion", "Content Suggestion"),
    ("open-intro", "Open Intro"),
    ("close-intro", "Close Intro"),
    ("close-concept", "Close Concept"),
    ("next-intro", "Next Intro Slide"),
    ("prev-intro", "Previous Intro Slide"),
    ("save-layout", "Save Layout"),
    ("reset-layout", "Reset Layout"),
    ("run-dagre", "Run Dagre"),
    ("reset-progress", "Reset Progress"),
    ("reset-pan", "Reset Pan"),
    ("feedback-button", "Feedback Button"),
    ("slack-button", "Slack Button"),
]


class ButtonPressModel(models.Model):
    user_id = models.TextField(help_text="User ID of the user who pressed the button")
    session_id = models.TextField(help_text="session_key of the session the button was pressed in")
    page_extension = models.TextField(
        help_text="Extension of the page the user was on when the button was pressed"
    )
    button_name = models.TextField(
        help_text="Name of the button pressed",
        choices=ALL_BUTTONS,
    )
    timestamp = models.DateTimeField(auto_now=True)
