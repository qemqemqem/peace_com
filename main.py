"""
PEACE_COM: A CLI Dungeon Crawler
1980s Cyberpunk - Dwarves & Elves on the Moon

Entry point.
"""

from dotenv import load_dotenv

load_dotenv()

from game import run_game


def main():
    run_game()


if __name__ == "__main__":
    main()
