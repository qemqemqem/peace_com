"""
CLI display functions for PEACE_COM.
"""

SEPARATOR = "═" * 60


def print_title():
    """Print the game title screen."""
    print(SEPARATOR)
    print("  PEACE_COM: LUNAR DUNGEON CRAWLER")
    print("  [ 1987 - Luna Station Omega - Sector 7 ]")
    print(SEPARATOR)
    print("\nInitializing neural link...")
    print("Type 'quit' to exit the simulation.\n")


def print_separator():
    """Print a visual separator."""
    print("\n" + SEPARATOR + "\n")


def print_response(text: str):
    """Print an LLM response."""
    print()
    print(text)


def print_goodbye():
    """Print the exit message."""
    print("\nDisconnecting from neural link...")
    print("Thanks for playing PEACE_COM.")


def get_input() -> str:
    """Get user input."""
    return input("> ").strip()
