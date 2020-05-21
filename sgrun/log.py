"""
Tries to get a seatgeek verified (TM) logger for logging. If none is installed,
uses the default python logger.
"""
try:
    from sglib.log import getLogger
except ImportError:
    try:
        from sglog.log import getLogger
    except ImportError:
        from logging import getLogger


get_logger = getLogger
