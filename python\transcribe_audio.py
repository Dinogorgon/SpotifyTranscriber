import logging
    
    # Configure logging for persistent error collection
    # This logger will write full traceback to a file for debugging and monitoring
    logging.basicConfig(
        level=logging.ERROR,
        filename='transcription_errors.log', # Or configure via environment variable for production
        format='%(asctime)s - %(levelname)s - %(message)s',
        encoding='utf-8'
    )
        logging.error("Invalid script usage: Not enough arguments provided. Args: %s", sys.argv)
        logging.error("Audio file not found: %s", audio_path)
        except Exception as cleanup_e:
            logging.exception("Failed to clean up transcriber after main error.")
        # Original error message for the caller
        error_message = str(e)
        print(json.dumps({'error': error_message}), file=sys.stderr)
        
        # Log the full exception traceback for security monitoring and debugging
        logging.exception("An unexpected error occurred during transcription of '%s': %s", audio_path, error_message)