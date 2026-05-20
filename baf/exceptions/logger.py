import logging

# Configure the logger
logger = logging.getLogger("BESSER Agentic Framework")
logger.setLevel(logging.DEBUG)  # Set the logging level

# Create handlers
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler("application.log", encoding='utf-8')

# Set logging levels for handlers
console_handler.setLevel(logging.DEBUG)
file_handler.setLevel(logging.DEBUG)

# Create formatters
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)
