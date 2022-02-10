from datetime import datetime

import numpy as np
import pytz
from django.db import models
from django.db.models import UniqueConstraint

from accounts.models import User
from knowledge_maps.models import Concept
from learney_backend.base_models import UUIDModel
from questions.inference import GaussianParams


class InferredKnowledgeState(UUIDModel):
    user = models.ForeignKey(
        User,
        help_text="User who this knowledge state refers to",
        on_delete=models.CASCADE,
        related_name="knowledge_states",
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
    highest_level_achieved = models.FloatField(
        help_text="We don't want users' knowledge to seemingly drop so precipitously "
        "between sessions, so we keep track of the highest level achieved by them"
    )

    last_updated = models.DateTimeField(
        auto_now=True, help_text="Time that the knowledge state was last updated"
    )

    class Meta:
        constraints = [UniqueConstraint(fields=["user", "concept"], name="unique_user_concept")]

    @property
    def knowledge_state(self) -> GaussianParams:
        """Gets Gaussian distribution over the inferred knowledge state."""
        return GaussianParams(mean=self.mean, std_dev=self.std_dev)

    @property
    def knowledge_level(self) -> float:
        """The knowledge level of the user for the concept - the level above which we are 90% sure they are"""
        return self.knowledge_state.level

    @property
    def secs_since_last_updated(self) -> float:
        """Returns the number of seconds since the last update."""
        return (datetime.now().replace(tzinfo=pytz.utc) - self.last_updated).total_seconds()

    def get_display_knowledge_level(self, new_batch: bool) -> float:
        """Returns the knowledge level to display to the user."""
        show_updated_level = new_batch and self.secs_since_last_updated > 60 * 60 * 5  # 5 hours
        current_knowledge_level = (
            self._updated_std_dev_knowledge_level if show_updated_level else self.knowledge_level
        )
        return (current_knowledge_level + self.highest_level_achieved) / 2

    def get_updated_std_dev(self) -> float:
        """Between question batches, we update the knowledge level by increasing our uncertainty
        over the value of the knowledge state. This allows the learner's inferred knowledge level to
        change over time as our model doesn't account for this at present.

        Min std_dev = 0.4, max is 1.0, weighted by time since last update which is
         applied as an exponential decay.
        """
        min_std_dev: float = max(self.std_dev, 0.4)
        n_days = self.secs_since_last_updated / (60 * 60 * 24)
        # Weight by time passed since last update, with max std_dev of 1
        return min_std_dev + 0.6 * (1 - np.exp(-n_days / 10))

    def update_std_dev(self) -> None:
        """Updates the std_dev of the inferred knowledge state."""
        self.std_dev = self.get_updated_std_dev()
        self.save()

    @property
    def _updated_std_dev_knowledge_level(self) -> float:
        """Returns the updated distribution over knowledge levels based on the updated std_dev."""
        return GaussianParams(mean=self.mean, std_dev=self.get_updated_std_dev()).level
