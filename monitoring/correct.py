"""Bias-corrected failure prevalence for a monitoring period."""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np


def corrected_mode_prevalence(
    sample_preds: Sequence[int],
    test_labels: Sequence[int],
    test_preds: Sequence[int],
    confidence: float = 0.95,
    bootstrap_iterations: int = 20000,
    seed: int | None = 7,
) -> dict[str, Any]:
    """Bias-corrected live prevalence for one mode from sampled verdicts.

    The contract, precisely:

      1. ``raw`` is the uncorrected flag rate: ``mean(sample_preds)``.
      2. Compute the frozen judge's failure sensitivity and pass specificity
         from ``test_labels`` and ``test_preds``. Both use the monitoring
         convention that 1 means a failure is present. Failure sensitivity is
         the flagged fraction of human-labeled failures. Pass specificity is
         the unflagged fraction of human-labeled passes.
      3. Compute the Rogan-Gladen point estimate, then resample the held-out
         records and sampled predictions to obtain a percentile-bootstrap
         interval. Use a seeded NumPy generator so the committed result is
         reproducible.
      4. Resample the monitoring predictions and the paired held-out records
         independently with replacement. Keep their original sample sizes.
         Discard a draw if the correction cannot be computed. Clamp each
         retained estimate to [0, 1], then take the percentile interval.
         Raise ``ValueError`` if no replicate is valid.

    Args:
        sample_preds: the judge's 0/1 verdicts over the UNIFORM BASE sample
            only (never the risk strata; they are biased toward failure by
            design).
        test_labels: human labels for the frozen Homework 5 judge's test
            split.
        test_preds: the frozen judge's predictions on that test split.
        confidence: interval confidence level.
        bootstrap_iterations: number of percentile-bootstrap replicates.
        seed: numpy seed for a reproducible interval; None leaves the RNG
            untouched.

    Returns:
        {"raw", "corrected", "ci_low", "ci_high", "confidence",
         "failure_sensitivity", "pass_specificity", "n_sample"}
        with "corrected" clamped to [0, 1] and rates rounded to 4 places.

    Raises:
        ValueError: if an input is empty, the held-out inputs have different
            lengths, a value is not 0 or 1, a class is absent, the judge is
            missing a usable correction, or no bootstrap replicate is valid.
    """
    if any(len(values) == 0 for values in (sample_preds, test_labels, test_preds)):
        raise ValueError("sample and held-out inputs must be nonempty")
    if len(test_labels) != len(test_preds):
        raise ValueError("held-out labels and predictions must align")
    if any(value not in (0, 1) for values in (sample_preds, test_labels, test_preds) for value in values):
        raise ValueError("labels and predictions must be 0 or 1")
    if not 0 < confidence < 1 or bootstrap_iterations < 1:
        raise ValueError("confidence and bootstrap iterations must be positive and valid")

    sample = np.asarray(sample_preds, dtype=int)
    labels = np.asarray(test_labels, dtype=int)
    preds = np.asarray(test_preds, dtype=int)
    failures = labels == 1
    passes = labels == 0
    if not failures.any() or not passes.any():
        raise ValueError("held-out test data must include both classes")

    raw = float(sample.mean())
    sensitivity = float(preds[failures].mean())
    specificity = float((1 - preds[passes]).mean())
    denominator = sensitivity + specificity - 1
    if denominator <= 0:
        raise ValueError("judge has no usable prevalence correction")
    corrected = float(np.clip((raw + specificity - 1) / denominator, 0, 1))

    rng = np.random.default_rng(seed)
    sample_draws = sample[rng.integers(len(sample), size=(bootstrap_iterations, len(sample)))]
    test_indices = rng.integers(len(labels), size=(bootstrap_iterations, len(labels)))
    drawn_labels, drawn_preds = labels[test_indices], preds[test_indices]
    failure_counts = (drawn_labels == 1).sum(axis=1)
    pass_counts = (drawn_labels == 0).sum(axis=1)
    drawn_sensitivity = np.divide(
        ((drawn_labels == 1) & (drawn_preds == 1)).sum(axis=1),
        failure_counts,
        out=np.zeros(bootstrap_iterations),
        where=failure_counts > 0,
    )
    drawn_specificity = np.divide(
        ((drawn_labels == 0) & (drawn_preds == 0)).sum(axis=1),
        pass_counts,
        out=np.zeros(bootstrap_iterations),
        where=pass_counts > 0,
    )
    drawn_denominator = drawn_sensitivity + drawn_specificity - 1
    valid = (failure_counts > 0) & (pass_counts > 0) & (drawn_denominator > 0)
    if not valid.any():
        raise ValueError("no valid bootstrap replicate")
    drawn_corrected = np.clip(
        (sample_draws.mean(axis=1)[valid] + drawn_specificity[valid] - 1)
        / drawn_denominator[valid],
        0,
        1,
    )
    tail = (1 - confidence) / 2
    ci_low, ci_high = np.quantile(drawn_corrected, [tail, 1 - tail])
    return {
        "raw": round(raw, 4),
        "corrected": round(corrected, 4),
        "ci_low": round(float(ci_low), 4),
        "ci_high": round(float(ci_high), 4),
        "confidence": round(confidence, 4),
        "failure_sensitivity": round(sensitivity, 4),
        "pass_specificity": round(specificity, 4),
        "n_sample": len(sample),
    }
