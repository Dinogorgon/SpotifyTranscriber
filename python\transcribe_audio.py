import logging
# Configure logging for internal monitoring
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
        # Log the full exception for internal monitoring and debugging
        logging.error("An unhandled exception occurred during transcription.", exc_info=True)