# These values are intentionally kept together because they affect every route score.

# This is a coarse average road speed used to turn graph distance into a free-flow baseline.
# It is not meant to represent every street exactly; it just gives the routing layer one consistent unit conversion.
DEFAULT_SPEED_LIMIT_KMPH = 60.0

# Each segment gets a small fixed junction delay so routes with many short hops are not unrealistically favored.
DEFAULT_INTERSECTION_DELAY_SECONDS = 30.0

# A light congestion factor used when predicted flow is available.
# The multiplier is intentionally capped so one noisy prediction does not dominate route ranking.
DEFAULT_CONGESTION_SCALE = 0.35
MAX_CONGESTION_MULTIPLIER = 2.5
