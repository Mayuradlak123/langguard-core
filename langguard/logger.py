import logging
import sys
import os

# Create logs directory if it doesn't exist
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Create a custom logger
logger = logging.getLogger("langguard")
logger.setLevel(logging.INFO)

# Create handlers
c_handler = logging.StreamHandler(sys.stdout)
f_handler = logging.FileHandler(os.path.join(log_dir, "application.log"))

# Create formatters and add to handlers
format_str = logging.Formatter('%(levelname)s:     %(asctime)s - %(message)s')
c_handler.setFormatter(format_str)
f_handler.setFormatter(format_str)

# Add handlers to the logger
if not logger.handlers:
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

# Silence noisy libraries
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("watchfiles").setLevel(logging.WARNING)
