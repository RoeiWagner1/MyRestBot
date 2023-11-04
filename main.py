import sqlite3
from typing import Final
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext, Updater

TOKEN = 0
BOT_USERNAME: Final = '@MyRestList_bot'

# Read the token from the config file
with open('config.txt') as file:
    lines = file.readlines()
    for line in lines:
        key, value = line.strip().split('=')
        if key == 'TOKEN':
            TOKEN = value


# Connect to the SQLite database
conn = sqlite3.connect('restaurant_data.db')
cursor = conn.cursor()

# Create tables for visited and wishlist restaurants if they don't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS visited_restaurants (
        chat_id INTEGER,
        name TEXT,
        address TEXT,
        last_visited_date DATE,
        specific_dishes TEXT,
        comments TEXT,
        PRIMARY KEY (chat_id, name)
    )
''')
conn.commit()


cursor.execute('''
    CREATE TABLE IF NOT EXISTS wish_list (
        chat_id INTEGER,
        name TEXT,
        address TEXT,
        comments TEXT,
        PRIMARY KEY (chat_id, name)
    )
''')
conn.commit()


# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome, I'm your restaurant bot! \nMy goal is to help you not forget your favorite restaurants. \nHere you can add restaurants you liked to your favorites list, or restaurants you would like to visit to your wish list. \nDon't worry, you can always update, edit or remove them - type / to display all possible actions. \nHave fun :)")


async def add_to_visited(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    await context.bot.send_message(chat_id, "Please provide details about the restaurant you visited.\n\n" "Enter the name of the restaurant:")
    context.user_data['pending_action'] = 'restaurant_name_visited'  # Storing the current pending action


async def get_restaurant_info(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    await context.bot.send_message(chat_id, "Please enter the name of the restaurant you want details for:")
    context.user_data['pending_action'] = 'get_restaurant_name'  # Storing the current pending action


async def add_to_wishlist(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    await context.bot.send_message(chat_id, "Please provide details about the restaurant you want to add to your wish list.\n\n" "Enter the name of the restaurant:")
    context.user_data['pending_action'] = 'restaurant_name_wishlist'  # Storing the current pending action


async def view_wishlist(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id

    # Fetch all restaurants from the wish list for the current chat_id
    cursor.execute('SELECT * FROM wish_list WHERE chat_id = ?', (chat_id,))
    result = cursor.fetchall()

    if result:
        response_message = "<u>Your Wish List:</u>\n\n"
        for row in result:
            restaurant_name = row[1]  # Assuming name is in the second column
            address = row[2]  # Assuming address is in the third column
            comments = row[3]  # Assuming comments are in the fourth column

            response_message += f"<b>שם:</b> {restaurant_name}\n" \
                               f"<b>כתובת:</b> {address}\n" \
                               f"<b>הערות:</b> {comments}\n\n"

        await context.bot.send_message(chat_id, response_message, parse_mode=ParseMode.HTML)
    else:
        await context.bot.send_message(chat_id, "Your wish list is empty.")


async def view_favorites(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id

    # Fetch all restaurants from the wish list for the current chat_id
    cursor.execute('SELECT * FROM visited_restaurants WHERE chat_id = ?', (chat_id,))
    result = cursor.fetchall()

    if result:
        response_message = "<u>Your favorites:</u>\n\n"
        for row in result:
            restaurant_name = row[1]  # Assuming name is in the second column
            address = row[2]  # Assuming address is in the third column
            specific_dishes = row[4]  # Assuming comments are in the fifth column

            response_message += f"<b>שם:</b> {restaurant_name}\n" \
                               f"<b>כתובת:</b> {address}\n" \
                               f"<b>מנות אהובות:</b> {specific_dishes}\n\n"

        await context.bot.send_message(chat_id, response_message, parse_mode=ParseMode.HTML)
    else:
        await context.bot.send_message(chat_id, "Your wish list is empty.")


async def delete_restaurant(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    await context.bot.send_message(chat_id, "Which restaurant do you want to delete? Enter the name of the restaurant:")
    context.user_data['pending_action'] = 'delete_restaurant'


async def edit_restaurant(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    await context.bot.send_message(chat_id, "Which restaurant do you want to edit? \nEnter the name of the restaurant:")
    context.user_data['pending_action'] = 'edit_restaurant'


async def handle_user_input(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user_input = update.message.text

    if 'pending_action' in context.user_data:
        pending_action = context.user_data['pending_action']

        if pending_action == 'restaurant_name_visited':
            cursor.execute('SELECT * FROM visited_restaurants WHERE chat_id = ? AND name = ?',
                           (chat_id, user_input))
            result_visited = cursor.fetchone()

            # Check if the restaurant already exists in the wish list
            cursor.execute('SELECT * FROM wish_list WHERE chat_id = ? AND name = ?',
                           (chat_id, user_input))
            result_wishlist = cursor.fetchone()

            if result_visited or result_wishlist:
                await context.bot.send_message(chat_id, "This restaurant appears on one of your lists.")
                # Decide what to do next; possibly return or take some other action
            else:
                context.user_data['restaurant_name'] = user_input
                await context.bot.send_message(chat_id, "Enter the address of the restaurant:")
                context.user_data['pending_action'] = 'restaurant_address_visited'

        elif pending_action == 'restaurant_address_visited':
            context.user_data['restaurant_address'] = user_input
            await context.bot.send_message(chat_id, "Enter the last date you visited the restaurant (DD.MM.YYYY):")
            context.user_data['pending_action'] = 'last_visited_date'

        elif pending_action == 'last_visited_date':
            context.user_data['last_visited_date'] = user_input
            await context.bot.send_message(chat_id, "Enter specific dishes you liked at the restaurant:")
            context.user_data['pending_action'] = 'specific_dishes'

        elif pending_action == 'specific_dishes':
            context.user_data['specific_dishes'] = user_input
            await context.bot.send_message(chat_id, "Any comments or notes about the restaurant?")
            context.user_data['pending_action'] = 'comments'

        elif pending_action == 'comments':
            context.user_data['comments'] = user_input

            # Store gathered data into the visited_restaurants table
            cursor.execute('''
                INSERT OR REPLACE INTO visited_restaurants (chat_id, name, address, last_visited_date, specific_dishes, comments)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                chat_id,
                context.user_data['restaurant_name'],
                context.user_data['restaurant_address'],
                context.user_data['last_visited_date'],
                context.user_data['specific_dishes'],
                context.user_data['comments']
            ))
            conn.commit()

            await context.bot.send_message(chat_id, "Details of the visited restaurant added!\n"
                                              "You can use /getinfo to view details of a restaurant.")
            context.user_data.clear()  # Clearing user data

        elif pending_action == 'get_restaurant_name':
            context.user_data['restaurant_name'] = user_input

            user_id = update.message.chat_id
            restaurant_name = context.user_data['restaurant_name']

            cursor.execute('SELECT * FROM visited_restaurants WHERE name = ? AND chat_id = ?',
                           (restaurant_name, user_id))
            result = cursor.fetchone()

            if result:
                response_message = f"<b>{restaurant_name}</b>\n\n" \
                                   f"<b>כתובת:</b> {result[2]}\n" \
                                   f"<b>תאריך ביקור אחרון:</b> {result[3]}\n" \
                                   f"<b>מנות אהובות:</b> {result[4]}\n" \
                                   f"<b>הערות:</b> {result[5]}"
                await update.message.reply_text(text=response_message, parse_mode=ParseMode.HTML)
            else:
                await update.message.reply_text(
                    f"Sorry, '{restaurant_name}' not found in the list of restaurants you visited. Check if the restaurant appears on your wish list")

            context.user_data.clear()

        elif pending_action == 'restaurant_name_wishlist':
            cursor.execute('SELECT * FROM visited_restaurants WHERE chat_id = ? AND name = ?',
                           (chat_id, user_input))
            result_visited = cursor.fetchone()

            # Check if the restaurant already exists in the wish list
            cursor.execute('SELECT * FROM wish_list WHERE chat_id = ? AND name = ?',
                           (chat_id, user_input))
            result_wishlist = cursor.fetchone()

            if result_visited or result_wishlist:
                await context.bot.send_message(chat_id, "This restaurant appears on one of your lists.")
                # Decide what to do next; possibly return or take some other action
            else:
                context.user_data['restaurant_name'] = user_input
                await context.bot.send_message(chat_id, "Enter the address of the restaurant:")
                context.user_data['pending_action'] = 'restaurant_address_wishlist'

        elif pending_action == 'restaurant_address_wishlist':
            context.user_data['restaurant_address'] = user_input
            await context.bot.send_message(chat_id, "Any comments or notes about the restaurant?")
            context.user_data['pending_action'] = 'comments_wishlist'

        elif pending_action == 'comments_wishlist':
            context.user_data['comments'] = user_input

            # Store gathered data into the wish_list table
            cursor.execute('''
                INSERT OR REPLACE INTO wish_list (chat_id, name, address, comments)
                VALUES (?, ?, ?, ?)
            ''', (
                chat_id,
                context.user_data['restaurant_name'],
                context.user_data['restaurant_address'],
                context.user_data['comments']
            ))
            conn.commit()

            await context.bot.send_message(chat_id, "Restaurant added to your wish list!\n"
                                              "You can use /getwishlist to view your wish list.")
            context.user_data.clear()  # Clear user data after processing

        elif pending_action == 'delete_restaurant':
            user_input = update.message.text
            chat_id = update.message.chat_id

            # Check which table to delete from (visited_restaurants or wish_list)
            cursor.execute('SELECT * FROM visited_restaurants WHERE chat_id = ? AND name = ?', (chat_id, user_input))
            result_visited = cursor.fetchone()

            cursor.execute('SELECT * FROM wish_list WHERE chat_id = ? AND name = ?', (chat_id, user_input))
            result_wishlist = cursor.fetchone()

            # Deleting the restaurant if found
            if result_visited:
                cursor.execute('DELETE FROM visited_restaurants WHERE chat_id = ? AND name = ?', (chat_id, user_input))
                conn.commit()
                await context.bot.send_message(chat_id, f"The restaurant has been deleted from your favorites list.")
            elif result_wishlist:
                cursor.execute('DELETE FROM wish_list WHERE chat_id = ? AND name = ?', (chat_id, user_input))
                conn.commit()
                await context.bot.send_message(chat_id, f"The restaurant has been deleted from your wish-list.")
            else:
                await context.bot.send_message(chat_id, "The restaurant you want to delete was not found.")

        elif pending_action == 'edit_restaurant':
            user_input = update.message.text
            chat_id = update.message.chat_id

            cursor.execute('SELECT * FROM visited_restaurants WHERE chat_id = ? AND name = ?', (chat_id, user_input))
            result_visited = cursor.fetchone()

            cursor.execute('SELECT * FROM wish_list WHERE chat_id = ? AND name = ?', (chat_id, user_input))
            result_wishlist = cursor.fetchone()

            if result_visited:
                await context.bot.send_message(chat_id,
                                               "Which field do you want to edit? \n(name, address, last_visited_date, specific_dishes, comments)")
                context.user_data['pending_action'] = 'edit_visited'
                context.user_data['restaurant_name'] = user_input  # Store the restaurant name for the edit operation

            elif result_wishlist:
                await context.bot.send_message(chat_id, "Which field do you want to edit? \n(name, address, comments)")
                context.user_data['pending_action'] = 'edit_wishlist'
                context.user_data['restaurant_name'] = user_input  # Store the restaurant name for the edit operation

            else:
                await context.bot.send_message(chat_id, "The restaurant you want to edit was not found.")

        elif pending_action == 'edit_visited':
            user_input = update.message.text.lower()
            valid_fields_visited = ["name", "address", "last_visited_date", "specific_dishes", "comments"]

            if user_input in valid_fields_visited:
                field = user_input
                chat_id = update.message.chat_id

                await context.bot.send_message(chat_id, f"Enter the new {field.replace('_', ' ')} for the restaurant:")
                context.user_data['pending_action'] = f'edit_visited_{field}'

            else:
                await context.bot.send_message(chat_id, "Invalid field. Please select a valid field to edit.")

        elif pending_action == 'edit_wishlist':
            user_input = update.message.text.lower()
            valid_fields_wishlist = ["name", "address", "comments"]

            if user_input in valid_fields_wishlist:
                field = user_input
                chat_id = update.message.chat_id

                await context.bot.send_message(chat_id, f"Enter the new {field.replace('_', ' ')} for the restaurant:")
                context.user_data['pending_action'] = f'edit_wishlist_{field}'

            else:
                await context.bot.send_message(chat_id, "Invalid field. Please select a valid field to edit.")

        # Handler for 'visited' table field update
        elif pending_action.startswith('edit_visited_'):
            field = pending_action.split('_')[-1]
            user_input = update.message.text
            chat_id = update.message.chat_id
            restaurant_name = context.user_data['restaurant_name']

            cursor.execute(f'UPDATE visited_restaurants SET {field} = ? WHERE chat_id = ? AND name = ?',
                           (user_input, chat_id, restaurant_name))
            conn.commit()
            await context.bot.send_message(chat_id, f"Restaurant '{restaurant_name}' details updated.")

            context.user_data.clear()

        # Handler for 'wishlist' table field update
        elif pending_action.startswith('edit_wishlist_'):
            field = pending_action.split('_')[-1]
            user_input = update.message.text
            chat_id = update.message.chat_id
            restaurant_name = context.user_data['restaurant_name']

            cursor.execute(f'UPDATE wish_list SET {field} = ? WHERE chat_id = ? AND name = ?',
                           (user_input, chat_id, restaurant_name))
            conn.commit()

            await context.bot.send_message(chat_id, f"Restaurant '{restaurant_name}' details updated.")
            context.user_data.clear()

    else:
        if 'hello' in user_input.lower() or 'hey' in user_input.lower() or 'שלום' in user_input:
            await context.bot.send_message(chat_id, "Hello! \nNice to have you here :)")

        elif 'how are you' in user_input.lower() or "whats up" in user_input.lower() or 'מה קורה' in user_input:
            await context.bot.send_message(chat_id, "I'm good, thank you for asking!")

        else:
            await context.bot.send_message(chat_id, "Sorry, I didn't understand what you wrote :( \nI'm a bot so I respond to specific words or built-in commands that you can see by typing the character /")
            return


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'update {update} caused error {context.error}')


if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler("addvisited", add_to_visited))
    app.add_handler(CommandHandler('getinfo', get_restaurant_info))
    app.add_handler(CommandHandler("addtowishlist", add_to_wishlist))
    app.add_handler(CommandHandler("getwishlist", view_wishlist))
    app.add_handler(CommandHandler("getfavorites", view_favorites))
    app.add_handler(CommandHandler("delete", delete_restaurant))
    app.add_handler(CommandHandler("edit", edit_restaurant))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))

    # Error
    app.add_error_handler(error)

    # Polls the bot
    print('Polling...')
    app.run_polling(poll_interval=3)