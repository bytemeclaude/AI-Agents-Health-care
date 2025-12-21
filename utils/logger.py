import logging
import sys

# Configure logging
def get_logger(name: str):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def sanitize_log(message: str) -> str:
    """
    Simple sanitizer to mask potential PII in logs.
    In a real system, this would be more sophisticated or we'd avoid logging PII entirely.
    """
    # Placeholder for PII scrubbing logic
    # For now, we trust the caller not to log raw PII or we accept some risk in this demo.
    return message
