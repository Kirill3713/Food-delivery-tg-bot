# Импортируем модули
import telebot
from config import api_token
import logging
from telebot import types
import json
# Объявляем переменные
TOKEN = api_token
bot = telebot.TeleBot(TOKEN)
menu_items = [
        {"name": "Грибной суп", "price": "450 руб.", "photo": "mushroom_soup.png"},
        {"name": "Салат Цезарь", "price": "550 руб.", "photo": "caesar.png"},
        {"name": "Утка с апельсинами", "price": "700 руб.", "photo": "duck_orange.png"},
        {"name": "Бефстроганов", "price": "650 руб.", "photo": "stroganoff.png"},
        {"name": "Ризотто", "price": "500 руб.", "photo": "risotto.png"},
        {"name": "Тирамису", "price": "400 руб.", "photo": "tiramisu.png"},
        {"name": "Блины", "price": "300 руб.", "photo": "pancakes.png"},
        {"name": "Паста Карбонара", "price": "550 руб.", "photo": "carbonara.png"},
        {"name": "Гаспачо", "price": "350 руб.", "photo": "gazpacho.png"},
        {"name": "Фалафель", "price": "400 руб.", "photo": "falafel.png"}

]
ITEMS_PER_PAGE = 4
# Создаем функции
def button_menu() -> types.ReplyKeyboardMarkup:
    """
    Создаем клавиатуру.
    """
    logging.info("Основная клавиатура. (меню/корзина)")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button1 = types.KeyboardButton("Меню 🍴")
    button2 = types.KeyboardButton("Корзина 🧺")
    
    markup.add(button1, button2)

    return markup
def generate_keyboard(button_names, prefix):
    """
    Создание кнопок
    """
    logging.info(f"Создание клавиатуры с префиксом {prefix}.")
    keyboard = types.InlineKeyboardMarkup()

    for name in button_names:
        data = f"{prefix}: {name}"
        button = types.InlineKeyboardButton(f"{name}", callback_data=f"{data}")
        keyboard.add(button)

    return keyboard
def save_name(message):
    logging.info("Сохраняем имя клиента.")
    new_name = message.text

    bot.send_message(message.chat.id, "Введите, пожалуйста, Ваш номер телефона:")
    bot.register_next_step_handler_by_chat_id(message.chat.id, save_number)
def save_number(message):
    logging.info("Сохраняем номер телефона клиента.")
    new_number = message.text
def generate_markup(page:int=0):
    """
    Создаем стандартную клавиатуру.
    """
    logging.info("Пагинация для меню.") # пагинация - от page=страница, у меню появятся страницы и стрелочки
    markup = types.InlineKeyboardMarkup()
    start_index = page*ITEMS_PER_PAGE
    end_index = start_index + ITEMS_PER_PAGE
    dishes = [dish["name"] for dish in menu_items][start_index:end_index]
    for item in dishes:
        button = types.InlineKeyboardButton(item, callback_data=f"dish_{item}") # dishes.index(item)
        markup.add(button)
    if page > 0:
        markup.add(types.InlineKeyboardButton(text="↫", callback_data=f"page_{page-1}"))
    if end_index < len(menu_items):
        markup.add(types.InlineKeyboardButton(text="↬", callback_data=f"page_{page+1}"))

    return markup
def get_cart(client_id:int|str) -> list|None:
    """
    Получаем список заказанных клиентом блюд.
    """
    logging.info("Получаем корзину")
    with open("data.json", "r", encoding="utf-8") as json_file:
        data = json.load(json_file)
        for client in data["clients"]:
            if client["id"] == str(client_id):
                return client["cart"]
        return
def add_dish(client_id:int|str, item:str):
    """
    Добавляем блюдо в корзину.
    """
    logging.info(f"+1 к блюду {item}.")
    with open("data.json", "r", encoding="utf-8") as json_file:
        data = json.load(json_file)
    item_in_menu = False
    for client in data["clients"]:
        if client["id"] == str(client_id):
            id_client = client
            for dish in client["cart"]:
                if dish[0] == item:
                    data["clients"][data["clients"].index(client)]["cart"].remove(dish)
                    data["clients"][data["clients"].index(client)]["cart"].append([item, dish[1]+1])
                    item_in_menu = True
    if not item_in_menu:
        data["clients"][data["clients"].index(id_client)]["cart"].append([item, 1])
    with open("data.json", "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False)
def del_dish(client_id:int|str, item:str):
    """
    Уменьшаем количество блюда в корзине.
    """
    logging.info(f"-1 от блюда {item}.")
    with open("data.json", "r", encoding="utf-8") as json_file:
        data = json.load(json_file)
    for client in data["clients"]:
        if client["id"] == str(client_id):
            for dish in client["cart"]:
                if dish[0] == item:
                    if dish[1] > 1:
                        data["clients"][data["clients"].index(client)]["cart"].remove(dish)
                        data["clients"][data["clients"].index(client)]["cart"].append([item, dish[1]-1])
                    else:
                        data["clients"][data["clients"].index(client)]["cart"].remove(dish)

    with open("data.json", "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False)
# Декоратор
@bot.message_handler(commands=["start"])
def handle_start(message):
    logging.info("Начинаем работу бота")
    bot.send_message(message.chat.id, "Привет, закажи еду из ресторана прямо себе домой!", reply_markup=button_menu())
@bot.message_handler(commands=["add_info"])
def handle_add_info(message):
    logging.info("Сохраняем данные пользователя")
    bot.send_message(message.chat.id, "Введите, пожалуйста, Ваше имя:")
    bot.register_next_step_handler_by_chat_id(message.chat.id, save_name)
@bot.message_handler(func=lambda message: True)
def reply_on_keyboard_message(message):
    if message.text == "Меню 🍴":
        logging.info("Меню")
        bot.reply_to(message, "Вы зашли в меню.")
        bot.send_message(message.chat.id, "Основное меню:", reply_markup=generate_markup())
    elif message.text == "Корзина 🧺":
        logging.info("Корзина")

        items = get_cart(message.chat.id)
        markup = types.InlineKeyboardMarkup()

        for item in items:

            minus_button = types.InlineKeyboardButton("-", callback_data=f"minus_{item[0]}")
            name_button = types.InlineKeyboardButton(f"{item[0]} x{item[1]}", callback_data=f"name_{item}")
            plus_button = types.InlineKeyboardButton("+", callback_data=f"plus_{item[0]}")

            markup.add(minus_button, name_button, plus_button)

        bot.send_message(message.chat.id, "Корзина:", reply_markup=markup)
@bot.callback_query_handler(func=lambda call: True)
def quary_handler(call):
    if call.data.startswith("page_"):
        logging.info("Обработка пагинации.")
        text, page = call.data.split("_")
        markup = generate_markup(int(page))
        bot.edit_message_text("Выбор элемента: ", call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif call.data.startswith("dish_"):
        logging.info("Обработка добавления блюда через меню.")
        text, item = call.data.split("_")
        add_dish(call.message.chat.id, item)
        bot.send_message(call.message.chat.id, f"Блюдо '{item}' добавлено в корзину.")
    elif call.data.startswith("plus_"):
        logging.info("Обработка добавления блюда в корзине.")
        text, item = call.data.split("_")
        add_dish(call.message.chat.id, item)
        bot.send_message(call.message.chat.id, f"Блюда '{item}' на один больше.")
    elif call.data.startswith("minus_"):
        logging.info("Обраюобтка убавления блюда в корзине.")
        text, item = call.data.split("_")
        del_dish(call.message.chat.id, item)
        bot.send_message(call.message.chat.id, f"Блюда '{item}' на один меньше.")
# Точка входа
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Запуск программы . . . . .")
    bot.polling(non_stop=True)