import re
import sqlite3
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext, \
    CallbackQueryHandler

TOKEN = 0

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


async def display_main_menu(chat_id, context: CallbackContext):
    bold_text = "<b>Main Menu:</b>"
    keyboard = [
        [
            InlineKeyboardButton("My Lists", callback_data='mylists')
        ],
        [
            InlineKeyboardButton("Information", callback_data='info')
        ],
        [
            InlineKeyboardButton("Update List", callback_data='update')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id, text=bold_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    await context.bot.send_message(chat_id,
                                   text="Welcome! I'm WishDish, your restaurant bot :) \n\nMy aim is to ensure you never forget your favorite restaurants. \n\nYou can add the restaurants you love to your favorites list or the ones you wish to visit to your wish list. \n\nFeel free to update, edit, or remove them anytime. Enjoy!")
    await display_main_menu(chat_id, context)


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    await display_main_menu(chat_id, context)


async def get_restaurant_info(chat_id, context: CallbackContext):
    await context.bot.send_message(chat_id,
                                   "Let's check what I know about the restaurant you're looking for! \n\nPlease enter the name of the restaurant:")
    context.user_data['pending_action'] = 'get_restaurant_name'


async def view_wishlist(chat_id, context: CallbackContext):
    # Fetch all restaurants from the wish list for the current chat_id
    cursor.execute('SELECT * FROM wish_list WHERE chat_id = ? ORDER BY SUBSTR(address, INSTR(address, ",") + 2)',
                   (chat_id,))
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

        response_message += f"Press /menu to return to the Menu."
        await context.bot.send_message(chat_id, response_message, parse_mode=ParseMode.HTML)
    else:
        await context.bot.send_message(chat_id, "Your wish list is empty.")


async def view_favorites(chat_id, context: CallbackContext):
    # Fetch all restaurants from the wish list for the current chat_id
    cursor.execute('SELECT * FROM visited_restaurants WHERE chat_id = ? ORDER BY SUBSTR(address, INSTR(address, ",") + 2)',
                   (chat_id,))
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

        response_message += f"Press /menu to return to the Menu."
        await context.bot.send_message(chat_id, response_message, parse_mode=ParseMode.HTML)
    else:
        await context.bot.send_message(chat_id, "Your favorites list is empty.")


async def delete_restaurant(chat_id, context: CallbackContext):
    await context.bot.send_message(chat_id, "Which restaurant do you want to delete? \nEnter the name:")
    context.user_data['pending_action'] = 'delete_restaurant'


async def edit_restaurant(chat_id, context: CallbackContext):
    await context.bot.send_message(chat_id, "Which restaurant do you want to edit? \nEnter the name:")
    context.user_data['pending_action'] = 'edit_restaurant'


async def move_to_favorites(chat_id, context: CallbackContext):
    await context.bot.send_message(chat_id,
                                   "It's always exciting to move a restaurant from the wish list to the favorites :) \n\nWhich restaurant do you want to move?")
    context.user_data['pending_action'] = 'restaurant_name_to_move'  # Storing the current pending action


async def view_list(chat_id, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("Wish List", callback_data='wish_list_view'),
            InlineKeyboardButton("Favorites", callback_data='favorites_view')
        ],
        [
            InlineKeyboardButton("Back to Menu", callback_data='menu')
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id, "Choose a list:", reply_markup=reply_markup)


async def add(chat_id, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("Wish List", callback_data='wish_list_add'),
            InlineKeyboardButton("Favorites", callback_data='favorites_add')
        ],
        [
            InlineKeyboardButton("Back to Menu", callback_data='menu')
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id,
                                   text="Happy you've found a restaurant you like! \n\nIf you change your mind, at any time, simply press /menu to return to the Menu.")
    await context.bot.send_message(chat_id, "Select the list you want to add to:", reply_markup=reply_markup)


async def add_to_favorites(chat_id, context: CallbackContext):
    await context.bot.send_message(chat_id, "Enter the name of the restaurant:")
    context.user_data['pending_action'] = 'restaurant_name_visited'  # Storing the current pending action


async def add_to_wishlist(chat_id, context: CallbackContext):
    await context.bot.send_message(chat_id, "Enter the name of the restaurant:")
    context.user_data['pending_action'] = 'restaurant_name_wishlist'  # Storing the current pending action


async def update_rest(chat_id, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("Add Restaurant", callback_data='add')
        ],
        [
            InlineKeyboardButton("Edit Restaurant", callback_data='edit')
        ],
        [
            InlineKeyboardButton("Delete Restaurant", callback_data='delete')
        ],
        [
            InlineKeyboardButton("Move Restaurant To Favorites", callback_data='move')
        ],
        [
            InlineKeyboardButton("Back to Menu", callback_data='menu')
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id, "What would you like to do:", reply_markup=reply_markup)


async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = query.message.chat_id
    data = query.data

    if data == 'mylists':
        await view_list(chat_id, context)
    elif data == "menu":
        await display_main_menu(chat_id, context)
    elif data == 'info':
        await get_restaurant_info(chat_id, context)
    elif data == 'update':
        await update_rest(chat_id, context)
    elif data == 'wish_list_view':
        await view_wishlist(chat_id, context)
    elif data == 'favorites_view':
        await view_favorites(chat_id, context)
    elif data == 'add':
        await add(chat_id, context)
    elif data == 'wish_list_add':
        await add_to_wishlist(chat_id, context)
    elif data == 'favorites_add':
        await add_to_favorites(chat_id, context)
    elif data == 'edit':
        await edit_restaurant(chat_id, context)
    elif data == 'delete':
        await delete_restaurant(chat_id, context)
    elif data == 'move':
        await move_to_favorites(chat_id, context)
    elif data == 'yes_info':
        await get_restaurant_info(chat_id, context)
    elif data == 'yes_edit':
        await edit_restaurant(chat_id, context)
    elif data == 'yes_delete':
        await delete_restaurant(chat_id, context)
    elif data == 'no_info':
        context.user_data.clear()
        await display_main_menu(chat_id, context)
    elif data == 'no_edit' or data == 'no_delete':
        context.user_data.clear()
        await update_rest(chat_id, context)

    elif data == 'name_visited' or data == 'address_visited' or data == 'date_visited' or data == 'dishes_visited' or data == 'comments_visited':
        field = data.split("_", 1)[0]
        await context.bot.send_message(chat_id, f"Enter the new {field} for the restaurant:")
        if field == "date":
            field = "last visited date"
        if field == "dishes":
            field = "specific dishes"
        context.user_data['pending_action'] = f'edit_visited_{field}'

    elif data == 'name_wl' or data == 'address_wl' or data == 'comments_wl':
        field = data.split("_", 1)[0]
        await context.bot.send_message(chat_id, f"Enter the new {field} for the restaurant:")
        context.user_data['pending_action'] = f'edit_wishlist_{field}'


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
            user_input = update.message.text
            chat_id = update.message.chat_id

            if re.match(r'\d{2}\.\d{2}\.\d{4}', user_input):
                context.user_data['last_visited_date'] = user_input
                await context.bot.send_message(chat_id, "Enter specific dishes you liked at the restaurant:")
                context.user_data['pending_action'] = 'specific_dishes'
            else:
                await context.bot.send_message(chat_id,
                                               "Oops, you didn't type the date in the correct format, let's try again!")
                await context.bot.send_message(chat_id, "Enter the last date you visited the restaurant (DD.MM.YYYY):")

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

            await context.bot.send_message(chat_id,
                                           "Restaurant added to your favorites!\n\nIf you'd like to view the details you've entered, \nuse the 'Information' button to view the restaurant, or 'My Lists' to view the list. \n\nPress /menu to return to the Menu.")
            context.user_data.clear()  # Clearing user data

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

            await context.bot.send_message(chat_id,
                                           "Restaurant added to your wish list!\n\nIf you'd like to view the details you've entered, \nuse the 'Information' button to view the restaurant, or 'My Lists' to view the list. \n\nPress /menu to return to the Menu.")
            context.user_data.clear()  # Clear user data after processing

        elif pending_action == 'get_restaurant_name':
            context.user_data['restaurant_name'] = user_input
            user_id = update.message.chat_id
            restaurant_name = context.user_data['restaurant_name']

            cursor.execute('SELECT * FROM visited_restaurants WHERE name = ? AND chat_id = ?',
                           (restaurant_name, user_id))
            result_visited = cursor.fetchone()

            cursor.execute('SELECT * FROM wish_list WHERE name = ? AND chat_id = ?',
                           (restaurant_name, user_id))
            result_wishlist = cursor.fetchone()

            if result_visited:
                response_message = f"<u>This restaurant is on your favorites list</u>\n\n" \
                                   f"<b>{restaurant_name}</b>\n\n" \
                                   f"<b>כתובת:</b> {result_visited[2]}\n" \
                                   f"<b>תאריך ביקור אחרון:</b> {result_visited[3]}\n" \
                                   f"<b>מנות אהובות:</b> {result_visited[4]}\n" \
                                   f"<b>הערות:</b> {result_visited[5]}\n\n"
                response_message += f"Press /menu to return to the Menu."
                await update.message.reply_text(text=response_message, parse_mode=ParseMode.HTML)

            elif result_wishlist:
                response_message = f"<u>This restaurant is on your wish-list</u>\n\n" \
                                   f"<b>{restaurant_name}</b>\n\n" \
                                   f"<b>כתובת:</b> {result_wishlist[2]}\n" \
                                   f"<b>הערות:</b> {result_wishlist[3]}\n\n"
                response_message += f"Press /menu to return to the Menu."
                await update.message.reply_text(text=response_message, parse_mode=ParseMode.HTML)

            else:
                await update.message.reply_text(f"Sorry, the restaurant doesn't appear on any of your lists.")
                await update.message.reply_text(
                    f"If you want to add it, click on the 'Update List' button in the Menu (/menu).")
                keyboard = [
                    [
                        InlineKeyboardButton("Yes", callback_data='yes_info'),
                        InlineKeyboardButton("No", callback_data='no_info')
                    ],
                ]

                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(chat_id, "Would you like to try again?", reply_markup=reply_markup)

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
                await display_main_menu(chat_id, context)

            elif result_wishlist:
                cursor.execute('DELETE FROM wish_list WHERE chat_id = ? AND name = ?', (chat_id, user_input))
                conn.commit()
                await context.bot.send_message(chat_id, f"The restaurant has been deleted from your wish list.")
                await display_main_menu(chat_id, context)
            else:
                await context.bot.send_message(chat_id, "The restaurant you're trying to delete was not found.")
                keyboard = [
                    [
                        InlineKeyboardButton("Yes", callback_data='yes_delete'),
                        InlineKeyboardButton("No", callback_data='no_delete')
                    ],
                ]

                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(chat_id, "Would you like to try again?", reply_markup=reply_markup)

        elif pending_action == 'edit_restaurant':
            user_input = update.message.text
            chat_id = update.message.chat_id

            cursor.execute('SELECT * FROM visited_restaurants WHERE chat_id = ? AND name = ?', (chat_id, user_input))
            result_visited = cursor.fetchone()

            cursor.execute('SELECT * FROM wish_list WHERE chat_id = ? AND name = ?', (chat_id, user_input))
            result_wishlist = cursor.fetchone()

            if result_visited:
                keyboard = [
                    [
                        InlineKeyboardButton("Name", callback_data='name_visited')
                    ],
                    [
                        InlineKeyboardButton("Address", callback_data='address_visited')
                    ],
                    [
                        InlineKeyboardButton("Date", callback_data='date_visited')
                    ],
                    [
                        InlineKeyboardButton("Dishes", callback_data='dishes_visited')
                    ],
                    [
                        InlineKeyboardButton("Comments", callback_data='comments_visited')
                    ],
                    [
                        InlineKeyboardButton("Back to Menu", callback_data='menu')
                    ]
                ]

                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(chat_id, "Which field do you want to edit?:", reply_markup=reply_markup)
                context.user_data['restaurant_name'] = user_input  # Store the restaurant name for the edit operation

            elif result_wishlist:
                keyboard = [
                    [
                        InlineKeyboardButton("Name", callback_data='name_wl')
                    ],
                    [
                        InlineKeyboardButton("Address", callback_data='address_wl')
                    ],
                    [
                        InlineKeyboardButton("Comments", callback_data='comments_wl')
                    ],
                    [
                        InlineKeyboardButton("Back to Menu", callback_data='menu')
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(chat_id, "Which field do you want to edit?:", reply_markup=reply_markup)
                context.user_data['restaurant_name'] = user_input  # Store the restaurant name for the edit operation

            else:
                await context.bot.send_message(chat_id, "Sorry, the restaurant you're looking to edit wasn't found.")
                keyboard = [
                    [
                        InlineKeyboardButton("Yes", callback_data='yes_edit'),
                        InlineKeyboardButton("No", callback_data='no_edit')
                    ],
                ]

                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(chat_id, "Would you like to try again?", reply_markup=reply_markup)

        elif pending_action.startswith('edit_visited_'):
            field = pending_action.split('_')[-1].replace(' ', '_')
            user_input = update.message.text
            chat_id = update.message.chat_id
            restaurant_name = context.user_data['restaurant_name']

            cursor.execute(f'UPDATE visited_restaurants SET {field} = ? WHERE chat_id = ? AND name = ?',
                           (user_input, chat_id, restaurant_name))
            conn.commit()
            await context.bot.send_message(chat_id,
                                           f"Details updated! \nClick on 'Information' in the Menu (/menu) to view.")

            context.user_data.clear()

        elif pending_action.startswith('edit_wishlist_'):
            field = pending_action.split('_')[-1]
            user_input = update.message.text
            chat_id = update.message.chat_id
            restaurant_name = context.user_data['restaurant_name']

            cursor.execute(f'UPDATE wish_list SET {field} = ? WHERE chat_id = ? AND name = ?',
                           (user_input, chat_id, restaurant_name))
            conn.commit()

            await context.bot.send_message(chat_id,
                                           f"Details updated! \nClick on 'Information' in the Menu (/menu) to view.")
            context.user_data.clear()

        elif pending_action == 'restaurant_name_to_move':
            cursor.execute('SELECT * FROM wish_list WHERE chat_id = ? AND name = ?', (chat_id, user_input))
            result = cursor.fetchone()

            if result:
                cursor.execute(
                    'INSERT OR REPLACE INTO visited_restaurants (chat_id, name, address, last_visited_date, specific_dishes, comments) '
                    'VALUES (?, ?, ?, ?, ?, ?)',
                    (chat_id, result[1], result[2], None, None, None))
                conn.commit()

                cursor.execute('DELETE FROM wish_list WHERE chat_id = ? AND name = ?', (chat_id, result[1]))
                conn.commit()
                await context.bot.send_message(chat_id,
                                               f"The restaurant has been removed from your wish-list! \nI'll ask 3 more questions before adding it to your favorites :)")
                await context.bot.send_message(chat_id, "Enter the last date you visited the restaurant (DD.MM.YYYY):")
                context.user_data['pending_action'] = 'last_visited_date'
                context.user_data['restaurant_name'] = result[1]
                context.user_data['restaurant_address'] = result[2]
            else:
                await context.bot.send_message(chat_id, f"Couldn't find the restaurant in your wish-list.")

    else:
        if 'hello' in user_input.lower() or 'hey' in user_input.lower() or 'שלום' in user_input:
            await context.bot.send_message(chat_id, "Hello! \nNice to have you here :)")

        elif 'how are you' in user_input.lower() or "whats up" in user_input.lower() or 'מה קורה' in user_input:
            await context.bot.send_message(chat_id, "I'm good, thank you for asking!")

        else:
            await context.bot.send_message(chat_id,
                                           "Sorry, I didn't catch that. \nI respond only to specific words or built-in commands \n\nIf you've entered a restaurant name, select the 'Information' button in the Menu (/menu) and try again.")
            return


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'update {update} caused error {context.error}')


if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('menu', menu_command))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))

    # Error
    app.add_error_handler(error)

    # Polls the bot
    print('Polling...')
    app.run_polling(poll_interval=3)
