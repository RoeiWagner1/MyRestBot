import asyncio
import unittest
from unittest.mock import AsyncMock
from telegram import Message
from datetime import datetime
from main import *


class TestBot(unittest.TestCase):
    def test_start_command(self):
        async def run_test():
            # Create a mock Update object to simulate the /start command
            update = Update(
                update_id=12345,
                message=Message(
                    message_id=54321,
                    chat=AsyncMock(),  # Use AsyncMock for async behaviors
                    text='/start',  # Simulating the /start command
                    date=datetime.now()
                )
            )

            # Simulate the context and call the start command function
            context = AsyncMock()
            await start_command(update, context)

            # Check the calls made to send_message method
            send_message_calls = context.bot.send_message.call_args_list

            # Replace these with actual expected responses
            expected_welcome_message = "Welcome! I'm WishDish, your restaurant bot :) \n\nMy aim is to ensure you never forget your favorite restaurants. \n\nYou can add the restaurants you love to your favorites list or the ones you wish to visit to your wish list. \n\nFeel free to update, edit, or remove them anytime. Enjoy!"
            expected_welcome_message = expected_welcome_message.replace("\n", " ")
            expected_main_menu = "Main Menu:"

            # Check if the expected messages are present in the calls made to send_message
            welcome_message_called = False
            main_menu_called = False
            buttons_called = False

            for call in send_message_calls:
                call_str = str(call)

                # Extracting the text part from the string representation
                call_args = call_str.split("text='")
                text_start = call_str.find("text=\"")

                if len(call_args) > 1:
                    message_text = call_args[1].split("'", 1)[0]
                    if expected_main_menu in message_text:
                        main_menu_called = True
                    buttons_called = "My Lists" in call_str and "Information" in call_str and "Update List" in call_str

                if text_start != -1:
                    text_start += len("text=\"")
                    text_end = call_str.find("\"", text_start)
                    message_text = call_str[text_start:text_end]
                    message_text = message_text.replace("\\n", " ")
                    if expected_welcome_message.lower() in message_text.lower():
                        welcome_message_called = True

            if not welcome_message_called:
                print("start command - expected welcome message not sent")
            if not main_menu_called:
                print("start command - expected main menu not sent")
            if not buttons_called:
                print("start command - expected buttons not found after the main menu message")
            if welcome_message_called and main_menu_called and buttons_called:
                print("start command ---> OK!")

        # Run the test asynchronously
        asyncio.run(run_test())


if __name__ == '__main__':
    unittest.main()


