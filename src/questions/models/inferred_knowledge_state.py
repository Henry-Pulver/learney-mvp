from django.db import models

from accounts.models import User
from knowledge_maps.models import Concept
from learney_backend.base_models import UUIDModel
from questions.inference import GaussianParams


class InferredKnowledgeState(UUIDModel):
    user = models.ForeignKey(
        User, help_text="User who this knowledge state refers to", on_delete=models.CASCADE
    )
    concept = models.ForeignKey(
        Concept,
        on_delete=models.SET_NULL,
        null=True,
        related_name="user_knowledge_states",
        help_text="The concept that this knowledge state refers to",
    )
    # The inferred knowledge state is a Gaussian with below mean and variance
    mean = models.FloatField(help_text="Mean of the inferred knowledge state distribution")
    std_dev = models.FloatField(
        help_text="Standard deviation of the inferred knowledge state distribution"
    )

    last_updated = models.DateTimeField(
        auto_now=True, help_text="Time that the knowledge state was last updated"
    )

    @property
    def knowledge_state(self) -> GaussianParams:
        return GaussianParams(mean=self.mean, std_dev=self.std_dev)
