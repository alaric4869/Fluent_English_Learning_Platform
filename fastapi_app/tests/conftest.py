import os


# Test runs must never inherit a locally enabled network provider from `.env`.
# An explicit process-level override remains possible for a dedicated integration run.
os.environ.setdefault("ENGLISH_TOOL_AI_PROVIDER", "disabled")
