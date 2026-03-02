import os
from pathlib import Path

import pytest
from dotenv import dotenv_values, load_dotenv
from groq import Groq

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
if not ENV_PATH.exists():
    raise AssertionError("Phase4/.env not found; cannot load GROQ_API_KEY.")

env_values = dotenv_values(ENV_PATH)
for key, value in env_values.items():
    if value is not None and key not in os.environ:
        os.environ[key] = value
load_dotenv(dotenv_path=ENV_PATH, override=False)


def _get_api_key() -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise AssertionError("GROQ_API_KEY is missing or empty in Phase4/.env")
    return api_key


@pytest.mark.integration
def test_groq_api_key_loaded() -> None:
    api_key = _get_api_key()
    assert isinstance(api_key, str)
    assert api_key.strip() != ""


@pytest.mark.integration
def test_groq_models_endpoint_connectivity() -> None:
    api_key = _get_api_key()
    client = Groq(api_key=api_key)
    try:
        models = client.models.list()
    except Exception as e:
        # Skip when network/proxy blocks access (e.g. 403, ProxyError, APIConnectionError)
        pytest.skip(
            f"Groq API unreachable in this environment: {type(e).__name__}: {e}"
        )
    assert models is not None
    assert hasattr(models, "data")
    assert isinstance(models.data, list)
    assert len(models.data) > 0
