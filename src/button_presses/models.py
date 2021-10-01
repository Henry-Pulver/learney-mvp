# from django.db import models
#
#
# ALL_BUTTONS = [
#     "log-in",
#     "log-out",
#     "make-suggestion",
#
# ]
# # raise NotImplementedError("NOT ALL BUTTONS LISTED!!")
#
# class ButtonPressModel(models.Model):
#     user_id = models.TextField(help_text="User ID of the user who pressed the button")
#     session_id = models.TextField(help_text="session_key of the session the button was pressed in")
#     page_url = models.URLField(help_text="URL of the page the button was on when pressed")
#     button_name = models.TextField(
#         help_text="Name of the button pressed",
#         choices=ALL_BUTTONS,
#     )
#     timestamp = models.DateTimeField(auto_now=True)
