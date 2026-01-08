"""
Unit tests for PEACE_COM dungeon crawler.
"""

import unittest
from unittest.mock import patch, MagicMock

from config import MODEL, QUIT_COMMANDS
from prompts import SYSTEM_PROMPT
from game import create_session
from llm import get_response
from ui import print_separator, SEPARATOR


class TestConfig(unittest.TestCase):
    """Tests for configuration."""

    def test_model_is_set(self):
        """Model should be configured."""
        self.assertIsInstance(MODEL, str)
        self.assertIn("claude", MODEL.lower())

    def test_quit_commands_exist(self):
        """Quit commands should be defined."""
        self.assertIn("quit", QUIT_COMMANDS)
        self.assertIn("exit", QUIT_COMMANDS)
        self.assertIn("q", QUIT_COMMANDS)


class TestCreateSession(unittest.TestCase):
    """Tests for create_session function."""

    def test_returns_list(self):
        """Session should be a list."""
        session = create_session()
        self.assertIsInstance(session, list)

    def test_contains_system_message(self):
        """Session should start with system message."""
        session = create_session()
        self.assertEqual(len(session), 1)
        self.assertEqual(session[0]["role"], "system")

    def test_system_message_has_prompt(self):
        """System message should contain the game prompt."""
        session = create_session()
        self.assertEqual(session[0]["content"], SYSTEM_PROMPT)


class TestGetResponse(unittest.TestCase):
    """Tests for get_response function."""

    @patch("llm.litellm.completion")
    def test_calls_litellm_with_correct_model(self, mock_completion):
        """Should call litellm with the configured model."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_completion.return_value = mock_response

        messages = [{"role": "system", "content": "test"}]
        get_response(messages)

        mock_completion.assert_called_once_with(
            model=MODEL,
            messages=messages,
        )

    @patch("llm.litellm.completion")
    def test_returns_message_content(self, mock_completion):
        """Should return the message content from the response."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "The dwarf looks at you suspiciously."
        mock_completion.return_value = mock_response

        messages = [{"role": "system", "content": "test"}]
        result = get_response(messages)

        self.assertEqual(result, "The dwarf looks at you suspiciously.")


class TestUI(unittest.TestCase):
    """Tests for UI functions."""

    def test_separator_constant(self):
        """Separator should be defined."""
        self.assertIn("═", SEPARATOR)
        self.assertEqual(len(SEPARATOR), 60)

    @patch("builtins.print")
    def test_print_separator(self, mock_print):
        """Should print a visual separator."""
        print_separator()
        mock_print.assert_called_once()
        call_arg = mock_print.call_args[0][0]
        self.assertIn("═", call_arg)


class TestGameLoop(unittest.TestCase):
    """Integration tests for the main game loop."""

    @patch("game.get_response")
    @patch("game.get_input")
    @patch("builtins.print")
    def test_quit_exits_loop(self, mock_print, mock_input, mock_llm):
        """Typing 'quit' should exit the game."""
        mock_llm.return_value = "Welcome to the moon, adventurer."
        mock_input.return_value = "quit"

        from game import run_game
        run_game()

        # Verify goodbye message was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        goodbye_printed = any("Thanks for playing" in call for call in print_calls)
        self.assertTrue(goodbye_printed)

    @patch("game.get_response")
    @patch("game.get_input")
    @patch("builtins.print")
    def test_exit_command_works(self, mock_print, mock_input, mock_llm):
        """Typing 'exit' should also exit the game."""
        mock_llm.return_value = "Welcome to the moon, adventurer."
        mock_input.return_value = "exit"

        from game import run_game
        run_game()

        print_calls = [str(call) for call in mock_print.call_args_list]
        goodbye_printed = any("Thanks for playing" in call for call in print_calls)
        self.assertTrue(goodbye_printed)

    @patch("game.get_response")
    @patch("game.get_input")
    @patch("builtins.print")
    def test_q_command_works(self, mock_print, mock_input, mock_llm):
        """Typing 'q' should also exit the game."""
        mock_llm.return_value = "Welcome to the moon, adventurer."
        mock_input.return_value = "q"

        from game import run_game
        run_game()

        print_calls = [str(call) for call in mock_print.call_args_list]
        goodbye_printed = any("Thanks for playing" in call for call in print_calls)
        self.assertTrue(goodbye_printed)

    @patch("game.get_response")
    @patch("game.get_input")
    @patch("builtins.print")
    def test_user_action_calls_llm(self, mock_print, mock_input, mock_llm):
        """User actions should trigger LLM responses."""
        mock_llm.return_value = "You see a neon sign flickering."
        # First call returns action, second call returns quit
        mock_input.side_effect = ["look around", "quit"]

        from game import run_game
        run_game()

        # LLM should be called twice: once for opening, once for action
        self.assertEqual(mock_llm.call_count, 2)

    @patch("game.get_response")
    @patch("game.get_input")
    @patch("builtins.print")
    def test_empty_input_is_ignored(self, mock_print, mock_input, mock_llm):
        """Empty input should not trigger LLM call."""
        mock_llm.return_value = "Welcome."
        mock_input.side_effect = ["", "", "quit"]

        from game import run_game
        run_game()

        # LLM should only be called once for the opening
        self.assertEqual(mock_llm.call_count, 1)


class TestMessageHistory(unittest.TestCase):
    """Tests for message history management."""

    @patch("game.get_response")
    @patch("game.get_input")
    @patch("builtins.print")
    def test_messages_accumulate(self, mock_print, mock_input, mock_llm):
        """Messages should accumulate in history."""
        mock_llm.return_value = "Response from LLM"
        mock_input.side_effect = ["action 1", "action 2", "quit"]

        from game import run_game
        run_game()

        # LLM should be called 3 times: opening + 2 actions
        self.assertEqual(mock_llm.call_count, 3)

        # The final messages list should have all the conversation
        # Note: list is passed by reference, so we see final state
        final_messages = mock_llm.call_args_list[-1][0][0]

        # Final state: system, user (initial), assistant, user, assistant, user, assistant (7 total)
        self.assertEqual(len(final_messages), 7)
        self.assertEqual(final_messages[0]["role"], "system")
        self.assertEqual(final_messages[1]["role"], "user")  # Initial prompt
        self.assertEqual(final_messages[2]["role"], "assistant")
        self.assertEqual(final_messages[3]["role"], "user")
        self.assertEqual(final_messages[3]["content"], "action 1")
        self.assertEqual(final_messages[5]["role"], "user")
        self.assertEqual(final_messages[5]["content"], "action 2")


if __name__ == "__main__":
    unittest.main()
