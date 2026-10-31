import os
import pytest


# Dummy credentials used only by the test process.
os.environ["STUDENT_API_KEY"] = "test-only-key"

os.environ["JWT_SECRET_KEY"] = (
    "test-only-jwt-secret-at-least-32-characters"
)

os.environ["ACCESS_TOKEN_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_DAYS"] = "7"

@pytest.fixture(autouse=True)
def reset_rate_limits():
    from rate_limit import limiter

    limiter.reset()

    try:
        yield
    finally:
        limiter.reset()