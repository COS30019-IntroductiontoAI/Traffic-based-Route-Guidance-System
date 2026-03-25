# Assignment-level assumptions used by the backend route engine.

DEFAULT_SPEED_LIMIT_KMPH = 60.0
DEFAULT_INTERSECTION_DELAY_SECONDS = 30.0

# A light congestion factor used when predicted flow is available.
# This is intentionally capped to keep estimated times stable.
DEFAULT_CONGESTION_SCALE = 0.35
MAX_CONGESTION_MULTIPLIER = 2.5
