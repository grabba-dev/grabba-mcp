from .server import main # Import your async main function from server.py

def run_cli():
    """
    Synchronous wrapper to run the async main function.
    This is the function Poetry's entry point will call.
    """
    main()

if __name__ == "__main__":
    run_cli()