"""CP5 research experiment (not a bonus submission): compare step caps 8 and 2."""

from unittest.mock import patch

from lab8.runtime import run_react
from lab8.shapes import single


def run_claim(claim_id, *, seed, store_path, crash_at=None):
    def capped(*args, **kwargs):
        kwargs["max_steps"] = 2
        return run_react(*args, **kwargs)

    with patch.object(single, "run_react", capped):
        return single.run_claim(claim_id, seed=seed, store_path=store_path, crash_at=crash_at)
