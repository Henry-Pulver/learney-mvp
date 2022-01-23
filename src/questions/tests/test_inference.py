from typing import Tuple

import numpy as np
import pytest

from questions.inference import GaussianParams, MCMCInference

# Difficulties
OBSERVED_DIFFS = np.array([1, 3, 2, 2, 3, 3, 1, 2, 3, 1, 3, 2, 2, 3, 3, 1, 2, 3])
OBSERVED_PROBS = np.array([0.25] * 4 + [0.5] + [0.25] * 8 + [0.5] + [0.25] * 4)


def test_inference_without_observations():
    mcmc_low_narrow = MCMCInference(GaussianParams(0, 0.25))
    with pytest.raises(AssertionError):
        mcmc_low_narrow.run_mcmc_inference(
            difficulties=np.array([]),
            guess_probs=np.array([]),
            answers=np.array([]),
        )


@pytest.mark.parametrize("theta_params", [GaussianParams(0, 0.25), GaussianParams(5, 2)])
def test_empty_predictions(theta_params: GaussianParams):
    mcmc = MCMCInference(theta_params)
    with pytest.raises(AssertionError):
        mcmc.prob_correct(np.ones(0), np.zeros(0))


@pytest.mark.parametrize(
    "answers",
    [
        np.array([1]),
        np.array([1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1]),
        np.array([1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1]),
    ],
)
@pytest.mark.parametrize(
    "questions_to_predict",
    [
        (np.ones(1), np.zeros(1)),
        (np.random.randint(0, 4, 10), np.random.uniform(0.2, 0.5, 10)),
    ],
)
@pytest.mark.parametrize("theta_params", [GaussianParams(0, 0.25), GaussianParams(5, 1)])
def test_predictions_consistent(
    answers: np.ndarray,
    questions_to_predict: Tuple[np.ndarray, np.ndarray],
    theta_params: GaussianParams,
):
    mcmc_low_narrow = MCMCInference(theta_params)
    mcmc_low_narrow.run_mcmc_inference(
        difficulties=OBSERVED_DIFFS[: len(answers)],
        guess_probs=OBSERVED_PROBS[: len(answers)],
        answers=answers,
    )
    mcmc2 = MCMCInference(mcmc_low_narrow.inferred_theta_params)

    orig_mcmc_pred = mcmc_low_narrow.prob_correct(*questions_to_predict)

    mcmc2_pred = mcmc2.prob_correct(*questions_to_predict)

    assert orig_mcmc_pred.shape == mcmc2_pred.shape
    assert all(np.abs(orig_mcmc_pred - mcmc2_pred) < 0.05)
