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
LIST_OF_NUMBERS = {}
# Создаем функции
def button_menu() -> types.ReplyKeyboardMarkup:
    """
    Создаем клавиатуру.
    """
    logging.info("Основная клавиатура. (меню/корзина/заказать)")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button1 = types.KeyboardButton("Меню 🍴")
    button2 = types.KeyboardButton("Корзина 🧺")
    button3 = types.KeyboardButton("Заказать 📜")

    markup.add(button1, button2, button3)

    return markup
# def generate_keyboard(button_names, prefix):
#     """
#     Создание кнопок
#     """
#     logging.info(f"Создание клавиатуры с префиксом {prefix}.")
#     keyboard = types.InlineKeyboardMarkup()

#     for name in button_names:
#         data = f"{prefix}: {name}"
#         button = types.InlineKeyboardButton(f"{name}", callback_data=f"{data}")
#         keyboard.add(button)

#     return keyboard
def save_name(message):
    """
    handle_add_info, save_name и save_number сохраняют контактные данные клиента. 
    """
    logging.info("Сохраняем имя клиента.")
    new_name = message.text

    bot.send_message(message.chat.id, "Введите, пожалуйста, Ваш номер телефона:")
    bot.register_next_step_handler_by_chat_id(message.chat.id, save_number, new_name)
def save_number(message, name):
    """
    См. описание save_name.
    """
    logging.info("Сохраняем номер телефона клиента.")
    # Обрабатываем и проверяем номер
    new_number = message.text.replace("+", "").replace(" ", "").strip()
    if message.text[0] == "+" and len(message.text) > 10 and len(message.text) < 17 and message.text.isdigit():
        new_number = message.text
    else:
        bot.send_message(message.chat.id, "Вы ввели неправильный номер. Попробуйте еще раз.")
        return
    # Читаем информацию
    try:    
        with open("data.json", "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        data = {
            "clients": [
                {
                    "id": "0000000000",
                    "name": "Иван Иванович",
                    "phone": "+7 900 000 0000",
                    "cart": []
                }
            ]
        }
    # Обновляем и выгружаем данные
    try:
        with open("data.json", "w", encoding="utf-8") as json_file:
            for client in data["clients"]:
                if client["id"] == message.chat.id:
                    cart = data["clients"][data["clients"].index(client)]["cart"]
                    data["clients"].remove(client)
                    data["clients"].append(
                        {
                            "id": str(message.chat.id),
                            "name": name,
                            "phone": new_number,
                            "cart": cart
                        }
                    )
                    json.dump(data, json_file, ensure_ascii=False)
                    bot.send_message(message.chat.id, "Ваши данные успешно обновленны.")
                    return
            data["clients"].append(
                {
                    "id": str(message.chat.id),
                    "name": name,
                    "phone": new_number,
                    "cart": []
                }
            )
            json.dump(data, json_file, ensure_ascii=False)
            bot.send_message(message.chat.id, "Ваши данные успешно обновленны.")
    except FileNotFoundError:
        bot.send_message(message.chat.id, "Извините, произошла ошибка. Попробуйте, пожалуйста, еще раз. Выберите команду /add_info")
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
def get_cart(client_id:int|str) -> list[list[str|int]]|None:
    """
    Получаем список заказанных клиентом блюд.
    """
    logging.info("Получаем корзину")
    try:
        with open("data.json", "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
            for client in data["clients"]:
                if client["id"] == str(client_id):
                    return client["cart"]
            return
    except FileNotFoundError:
        return
def add_dish(client_id:int|str, item:str):
    """
    Добавляем блюдо в корзину.
    """
    logging.info(f"+1 к блюду {item}.")
    # Читаем информацию
    try:
        with open("data.json", "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        bot.send_message(client_id, "Извините, произошла ошибка. Пожалуйста, добавьте контактную информацию с помощью функции /add_info.")
        return "No Fata Error"
    # Флажок. True если есть в заказе нужного клиента
    item_in_menu = False
    for client in data["clients"]:
        if client["id"] == str(client_id):
            for dish in client["cart"]:
                if dish[0] == item:
                    # Прибавляем один к количеству
                    data["clients"][data["clients"].index(client)]["cart"].remove(dish)
                    data["clients"][data["clients"].index(client)]["cart"].append([item, dish[1]+1])
                    item_in_menu = True
    # Если False, то создаем новую запись
    if not item_in_menu:
        client_found = False
        for client in data["clients"]:
            if client["id"] == str(client_id):
                data["clients"][data["clients"].index(client)]["cart"].append([item, 1])
                client_found = True
        if not client_found:
            return "No Data Error"
    # Выгружаем данные
    try:
        with open("data.json", "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False)
    except FileNotFoundError:
        bot.send_message(client_id, "Извините, произошла ошибка. Попробуйте снова.")
        return "No Data Error"
def del_dish(client_id:int|str, item:str):
    """
    Уменьшаем количество блюда в корзине.
    """
    logging.info(f"-1 от блюда {item}.")
    try:
        with open("data.json", "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        bot.send_message(client_id, "Извините, произошла ошибка. Попробуйте еще раз.")
        return
    for client in data["clients"]:
        if client["id"] == str(client_id):
            for dish in client["cart"]:
                if dish[0] == item:
                    if dish[1] > 1:
                        data["clients"][data["clients"].index(client)]["cart"].remove(dish)
                        data["clients"][data["clients"].index(client)]["cart"].append([item, dish[1]-1])
                    else:
                        data["clients"][data["clients"].index(client)]["cart"].remove(dish)
    try:
        with open("data.json", "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False)
    except FileNotFoundError:
        bot.send_message(client_id, "Извините, произошла ошибка. Попробуйте еще раз.")
        return
def reply_on_location(message):
    """
    Функция для обработки и ответа на адрес.
    """
    logging.info("Принимаем адрес заказа")
    if message.content_type == 'text':
        bot.reply_to(message, f"Ваш заказ прибудет по адресу {message.text} через 5 минут.")
    elif message.content_type == 'location':
        bot.reply_to(message, f"Ваш заказ прибудет по координатам {message.location.latitude}, {message.location.longitude} через 5 минут.")
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
@bot.message_handler(commands=["help"])
def handle_help(message):
    logging.info("Справка")
    bot.send_message(message.chat.id, "Этот бот создан для выбора еды из ресторана и доставки ее по выбранному адресу.\n/start - Эта команда запускает бота.\n/add_info - Регистрация, для того чтобы мы смогли с Вами связаться.\n/help - Справка о боте.\n\nНажав на кнопку 'Меню', Вы сможете выбрать нужную еду. При выборе кнопки 'Корзина' Вам будет показан список Вашей еды. После нажатия на кнопку 'Заказать' и выборf опции 'Подтвердить' у Вас будет запрошен адрес и Вы сможете ожидать Ваш заказ.")
@bot.message_handler(func=lambda message: True)
def reply_on_keyboard_message(message):
    if message.text == "Меню 🍴":
        logging.info("Меню")
        bot.reply_to(message, "Основное меню:", reply_markup=generate_markup())
    elif message.text == "Корзина 🧺":
        logging.info("Корзина")

        global LIST_OF_NUMBERS
        LIST_OF_NUMBERS = {}
        items = get_cart(message.chat.id)
        if items == None or items == []:
            bot.send_message(message.chat.id, "Вы пока ничего не добавили в корзину.")
        else:
            markup = types.InlineKeyboardMarkup()
            
            for item in items:

                minus_button = types.InlineKeyboardButton("-", callback_data=f"minus_{item[0]}")
                name_button = types.InlineKeyboardButton(f"{item[0]} x{item[1]}", callback_data=f"name_{item}")
                plus_button = types.InlineKeyboardButton("+", callback_data=f"plus_{item[0]}")
                LIST_OF_NUMBERS[item[0]] = item[1]
                markup.add(minus_button, name_button, plus_button)

            bot.reply_to(message, "Корзина:", reply_markup=markup)
    elif message.text == "Заказать 📜":
        logging.info("Заказ")
        items = get_cart(message.chat.id)
        if items == None or items == []:
            bot.reply_to(message, "Вы пока ничего не добавили в корзину.")
        else:
            bot.reply_to(message, "Ваш заказ:")
            for item in items:
                bot.send_message(message.chat.id, f"◌ {item[0]} x{item[1]}")

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            button1 = types.KeyboardButton("Подтвердить ✓")
            button2 = types.KeyboardButton("Отменить ✕")

            markup.add(button1, button2)

            bot.send_message(message.chat.id, "Подтвердите правильность заказа:", reply_markup=markup)
    elif message.text == "Отменить ✕":
        logging.info("Заказ не подтвержден")
        bot.reply_to(message, "Вы можете вернуться и изменить заказ.", reply_markup=button_menu())
    elif message.text == "Подтвердить ✓":
        logging.info("Заказ подтвержден")
        bot.reply_to(message, "Введите, пожалуйста, адрес доставки текстом или геометкой Telegram.")
        bot.register_next_step_handler_by_chat_id(message.chat.id, reply_on_location)
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
        if add_dish(call.message.chat.id, item) != "No Data Error":
            bot.send_message(call.message.chat.id, f"Блюдо '{item}' добавлено в корзину.")
        else:
            bot.send_message(call.message.chat.id, "Пожалуйста, сначала добавьте контактную информацию с помощью функции /add_info.")
    elif call.data.startswith("plus_"):
        logging.info("Обработка добавления блюда в корзине.")
        text, item = call.data.split("_")
        add_dish(call.message.chat.id, item)

        items = get_cart(call.message.chat.id)
        if items == None or items == []:
            bot.send_message(call.message.chat.id, "Вы пока ничего не добавили в корзину.")
        else:
            markup = types.InlineKeyboardMarkup()
            
            for item in items:

                minus_button = types.InlineKeyboardButton("-", callback_data=f"minus_{item[0]}")
                name_button = types.InlineKeyboardButton(f"{item[0]} x{item[1]}", callback_data=f"name_{item}")
                plus_button = types.InlineKeyboardButton("+", callback_data=f"plus_{item[0]}")

                markup.add(minus_button, name_button, plus_button)

        if len(call.message.text) > 8:
            global LIST_OF_NUMBERS
            if call.message.text[9] == "+":
                bot.edit_message_text(f"Корзина: +{item[1]-LIST_OF_NUMBERS[item[0]]} к блюду '{item[0]}'", call.message.chat.id, call.message.message_id, reply_markup=markup)
            else:
                LIST_OF_NUMBERS[item[0]] = item[1]-1
                bot.edit_message_text(f"Корзина: +{item[1]-LIST_OF_NUMBERS[item[0]]} к блюду '{item[0]}'", call.message.chat.id, call.message.message_id, reply_markup=markup)
        else:
                bot.edit_message_text(f"Корзина: +1 к блюду '{item[0]}'", call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif call.data.startswith("minus_"):
        logging.info("Обработка убавления блюда в корзине.")
        text, item = call.data.split("_")
        del_dish(call.message.chat.id, item)
        items = get_cart(call.message.chat.id)
        if items == None or items == []:
            bot.send_message(call.message.chat.id, "Вы пока ничего не добавили в корзину.")
        else:
            markup = types.InlineKeyboardMarkup()
            
            for item in items:

                minus_button = types.InlineKeyboardButton("-", callback_data=f"minus_{item[0]}")
                name_button = types.InlineKeyboardButton(f"{item[0]} x{item[1]}", callback_data=f"name_{item}")
                plus_button = types.InlineKeyboardButton("+", callback_data=f"plus_{item[0]}")

                markup.add(minus_button, name_button, plus_button)

        if len(call.message.text) > 8:
            if call.message.text[9] == "-":
                bot.edit_message_text(f"Корзина: -{LIST_OF_NUMBERS[item[0]]-item[1]} от количества блюда '{item[0]}'", call.message.chat.id, call.message.message_id, reply_markup=markup)
            else:
                LIST_OF_NUMBERS[item[0]] = item[1]+1
                bot.edit_message_text(f"Корзина: -{LIST_OF_NUMBERS[item[0]]-item[1]} от количества блюда '{item[0]}'", call.message.chat.id, call.message.message_id, reply_markup=markup)
        else:
            bot.edit_message_text(f"Корзина: -1 от количества блюда '{item[0]}'", call.message.chat.id, call.message.message_id, reply_markup=markup)
# Точка входа
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Запуск программы . . . . .")
    bot.polling(non_stop=True)