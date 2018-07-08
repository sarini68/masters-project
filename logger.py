import logging
import sys

LOG_FORMAT = "[%(levelname)s]: %(message)s"
LOG_LEVEL = logging.DEBUG

logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(LOG_FORMAT))
handler.setLevel(LOG_LEVEL)
logger.addHandler(handler)

logging.getLogger("neo4j.bolt").setLevel(logging.CRITICAL)
