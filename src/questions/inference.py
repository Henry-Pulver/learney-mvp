from dataclasses import dataclass
from statistics import NormalDist
from typing import Dict, Optional
from warnings import warn

import numpy as np

import jax.numpy as jnp
import numpyro.distributions as dist
from jax import random
from numpyro import plate, sample
from numpyro.infer import MCMC, NUTS, Predictive


@dataclass
class GaussianParams:
    mean: float
    std_dev: float
    # The level is where CDF(user's knowledge state = level) = LEVEL_THRESHOLD
    LEVEL_THRESHOLD = 0.05

    def __post_init__(self):
        assert self.std_dev >= 0
        self._dist = NormalDist(mu=self.mean, sigma=self.std_dev)

    @property
    def level(self) -> float:
        return max(self._dist.inv_cdf(self.LEVEL_THRESHOLD), 0)


# This is the 'discrimination' parameter, how steep the logistic curve is. This has been
# set heuristically. This setting has 85% of the variation lie in the range +-0.5.
SPECIAL_K = 5

# Probability of getting the question wrong despite understanding the concept. A magic
# number, set heuristically.
MISTAKE_PROB = 0.05

# MCMC parameters.
# The number of warmup samples to take to reach steady-state
MCMC_NUM_WARMUP_SAMPLES = 2000
# The number of usable samples to take to measure the steady-state distribution
MCMC_NUM_SAMPLES = 1000


def answers_model(
    prior_params: GaussianParams,
    difficulties: np.ndarray,
    guess_probabilities: np.ndarray,
    answers: Optional[np.ndarray] = None,
):
    """
    Numpyro model for learner answers. Can either be used for observed data (answers present) or to
     predict new data (answers = None).

    Args:
        prior_params: prior mean and standard deviation over knowledge state
        difficulties: Question difficulties
        guess_probabilities: Probability of correctly guessing the answer
        answers: None if generative, otherwise the array of answers. 1 is correct and 0 incorrect
    """
    theta = sample("theta", dist.Normal(prior_params.mean, prior_params.std_dev))

    p = guess_probabilities + (1 - guess_probabilities - MISTAKE_PROB) / (
        1 + jnp.exp((difficulties - theta) * SPECIAL_K)
    )

    with plate("data", len(difficulties)):
        return sample("obs", dist.Bernoulli(p), obs=answers)


class MCMCInference:
    """Can run inference on observed answers or the predictive model based on parameters given."""

    def __init__(self, knowledge_state_prior: GaussianParams, random_seed: int = 1):
        self._theta_prior = knowledge_state_prior
        # Samples of theta from MCMC
        self._samples: Optional[Dict[str, np.ndarray]] = None
        self._seed = random_seed
        self._correct_probs: Optional[np.ndarray] = None

    def run_mcmc_inference(
        self,
        difficulties: np.ndarray,
        guess_probs: np.ndarray,
        answers: np.ndarray,
        num_samples: int = MCMC_NUM_SAMPLES,
    ) -> None:
        """Runs Markov-Chain Monte-Carlo using the `answers_model` to get a distribution over the
        latent knowledge state given the difficulties, guess-probabilities and answers given.

        Args:
            difficulties: difficulty of each question observed (num_observations,)
            guess_probs: probability of guessing each question correctly observed (num_observations,)
            answers: correctness of answers observed. 1 correct, 0 incorrect (num_observations,)
            num_samples: number of MCMC samples to take to approximate the distribution
        """
        assert num_samples > 0, f"Number of samples ({num_samples}) must be >0"
        assert all(guess_probs >= 0) and all(guess_probs <= 1), (
            f"`guess_probs` probabilities aren't all valid probability values (0 < p < 1)\n"
            f"guess_probs: {guess_probs}"
        )
        assert all(
            (answers == 0) + (answers == 1)
        ), f"`answers` aren't all either 0 or 1\nanswers: {answers}"
        assert difficulties.shape == guess_probs.shape == answers.shape, (
            f"Shapes of arrays (difficulties, guess_probs, answers) aren't all the same: "
            f"difficulties: {difficulties.shape}, guess_probs: {guess_probs.shape}, answers: {answers.shape}"
        )
        assert difficulties.shape != 0 and guess_probs.shape != 0 and answers.shape != 0, (
            "One or more of the arrays (difficulties, guess_probs, answers) are empty! "
            f"difficulties: {difficulties.shape}, guess_probs: {guess_probs.shape}, answers: {answers.shape}"
        )
        nuts_kernel = NUTS(answers_model)
        mcmc = MCMC(
            nuts_kernel,
            num_warmup=MCMC_NUM_WARMUP_SAMPLES,
            num_samples=num_samples,
            progress_bar=False,
        )
        mcmc.run(random.PRNGKey(self._seed), self._theta_prior, difficulties, guess_probs, answers)
        self._samples = mcmc.get_samples()

    @property
    def inferred_theta_params(self) -> GaussianParams:
        if self._samples is None:
            warn("First run MCMC to get inferred latent variable values")
            return self._theta_prior
        return GaussianParams(
            float(np.mean(self._samples["theta"])), np.sqrt(np.var(self._samples["theta"]))
        )

    @property
    def correct_probs(self) -> np.ndarray:
        if self._correct_probs is None:
            warn("First run calculate_correct_probs() to get the probability the user is correct")
        return self._correct_probs

    def calculate_correct_probs(
        self,
        difficulties: np.ndarray,
        guess_probs: np.ndarray,
        num_samples: int = MCMC_NUM_SAMPLES,
    ) -> np.ndarray:
        """Given the distribution over theta, this predicts the probabilities of getting several
        questions correct.

        Args:
            difficulties: difficulty of each question (num_questions,)
            guess_probs: probability of guessing each question correctly observed (num_questions,)
            num_samples: number of MCMC samples to take to approximate the distribution

        Returns: probability of getting each question correct
        """
        assert difficulties.shape == guess_probs.shape, (
            f"Shapes of difficulties {difficulties.shape} and probability of "
            f"guess {guess_probs.shape} arrays are different - they must match!"
        )
        assert difficulties.shape != 0, (
            f"Arrays given to predict probabilities for are empty! "
            f"difficulties.shape={difficulties.shape}, guess_probs.shape={guess_probs.shape}"
        )

        # Using the samples is slightly quicker, so supporting using either and picking whichever will be fastest
        predictive = (
            Predictive(answers_model, self._samples)
            if self._samples is not None
            else Predictive(answers_model, num_samples=num_samples)
        )
        samples_predictive = predictive(
            random.PRNGKey(self._seed), self._theta_prior, difficulties, guess_probs
        )
        self._correct_probs = np.mean(samples_predictive["obs"], 0)
        return self._correct_probs
