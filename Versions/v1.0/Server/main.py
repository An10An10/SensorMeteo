import telebot
import threading
from flask import Flask, request
from database_module import *
from telebot import types, apihelper
from meteo_module import get_weather_full

apihelper.proxy = {'https': 'socks5h://127.0.0.1:25590'}

TOKEN = "ТОКЕН БОТА"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/update', methods=['POST'])
def update_data():
    try:
        sensor_id = request.headers.get('id')
        raw_data = request.data.decode('utf-8')
        t_str, h_str, p_str = raw_data.split(',')
        
        save_measurement(int(sensor_id), float(t_str), float(h_str), float(p_str))
        return "OK", 200
    except Exception as e:
        print(f"Ошибка приема: {e}")
        return "Error", 400


@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    create_user(user_id, message.from_user.first_name)
    
    text = (f"Привет, {message.from_user.first_name}!\n\n"
            f"Для работы прогноза погоды нужны ваши координаты.\n"
            f"Пожалуйста, введите их в формате: **широта,долгота**\n"
            f"Например: `55.75,37.61` (это Москва)")
    
    msg = bot.send_message(user_id, text, parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_region_step)


@bot.message_handler(commands=['setregion'])
def set_region_command(message):
    msg = bot.send_message(message.chat.id, "📍 Введите новые координаты (широта,долгота):")
    bot.register_next_step_handler(msg, process_region_step)

def process_region_step(message):
    user_id = message.from_user.id
    coord_input = message.text.strip()
    
    if update_user_mesto(user_id, coord_input):
        bot.send_message(user_id, f"Координаты успешно сохранены: `{coord_input}`\n"
                                  f"Теперь вы можете использовать /getweather или /mysens", 
                                  parse_mode="Markdown")
    else:
        msg = bot.send_message(user_id, "**Ошибка формата!**\n\n"
                                        "Введите координаты двумя числами через запятую.\n"
                                        "Пример: `52.52,13.41` (Берлин)")
        bot.register_next_step_handler(msg, process_region_step)


def get_status_text(val, unit, is_supported=True):
    if val == -1 or val == -1.0 or not is_supported:
        return "❌ _не поддерживается_"
    return f"`{val}` {unit}"

@bot.message_handler(commands=['mysens'])
def mysens_handler(m):
    data = get_full_user_data(m.from_user.id)
    if not data or not data['sensors']:
        bot.send_message(m.chat.id, "У вас нет привязанных сенсоров.")
        return
    
    text = f"🏠 **Регион:** `{data['mesto']}`\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    
    for s in data['sensors']:
        if 't' in s:
            t_text = get_status_text(s.get('t'), "°C")
            h_text = get_status_text(s.get('h'), "%")
            p_text = get_status_text(s.get('p'), "мм рт. ст.")

            text += (f"🔹 **ID {s['id']}**:\n"
                     f"🌡 Темп: {t_text}\n"
                     f"💧 Влаж: {h_text}\n"
                     f"🔽 Давл: {p_text}\n\n")
        else:
            text += f"🔸 **ID {s['id']}**: _нет данных от датчика_\n\n"
    
    bot.send_message(m.chat.id, text, parse_mode="Markdown")


@bot.message_handler(commands=['addsens'])
def addsens_handler(m):
    msg = bot.send_message(m.chat.id, "Введите ID нового сенсора:")
    bot.register_next_step_handler(msg, process_add_step)

def process_add_step(message):
    try:
        s_id = int(message.text)
        append_sensor_to_user(message.from_user.id, s_id)
        bot.send_message(message.chat.id, f"Сенсор {s_id} успешно привязан к вашему аккаунту.")
    except:
        bot.send_message(message.chat.id, "Ошибка: введите числовой ID.")

def process_region_step(message):
    update_user_mesto(message.from_user.id, message.text)
    bot.send_message(message.chat.id, f"Регион изменен на: {message.text}")


@bot.message_handler(commands=['addsens'])
def addsens_handler(m):
    msg = bot.send_message(m.chat.id, "Введите ID сенсора для добавления:")
    bot.register_next_step_handler(msg, process_add_step)

def process_add_step(message):
    try:
        s_id = int(message.text)
        append_sensor_to_user(message.from_user.id, s_id)
        bot.send_message(message.chat.id, f"Сенсор {s_id} добавлен!")
    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка! Введите только число ID.")


@bot.message_handler(commands=['setregion'])
def setregion_handler(m):
    msg = bot.send_message(m.chat.id, "Введите ваш город:")
    bot.register_next_step_handler(msg, process_region_step)

def process_region_step(message):
    update_user_mesto(message.from_user.id, message.text)
    bot.send_message(message.chat.id, f"Регион изменен на: {message.text}")


@bot.message_handler(commands=['delsens'])
def delsens_handler(m):
    msg = bot.send_message(m.chat.id, "Введите ID сенсора для удаления:")
    bot.register_next_step_handler(msg, process_del_step)

def process_del_step(message):
    try:
        s_id = int(message.text)
        if remove_sensor_from_user(message.from_user.id, s_id):
            bot.send_message(message.chat.id, f"Сенсор {s_id} удален.")
        else:
            bot.send_message(message.chat.id, "Сенсор не найден в вашем списке.")
    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка! Введите числовой ID.")


@bot.message_handler(commands=['getweather'])
def weather_choice(m):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Сейчас", callback_data="w_0"),
               types.InlineKeyboardButton("Через 3 часа", callback_data="w_3"))
    markup.add(types.InlineKeyboardButton("Через 6 часов", callback_data="w_6"),
               types.InlineKeyboardButton("Через 12 часов", callback_data="w_12"))
    
    bot.send_message(m.chat.id, "Выберите время прогноза:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('w_'))
def weather_callback(call):
    user_id = call.from_user.id
    hour_index = int(call.data.split('_')[1])
    
    user_data = get_full_user_data(user_id)
    if not user_data or not user_data['mesto'] or ',' not in user_data['mesto']:
        bot.answer_callback_query(call.id, "Сначала установите регион /setregion", show_alert=True)
        return

    lat, lon = map(float, user_data['mesto'].split(','))
    w = get_weather_full(lat, lon, hour_index)
    
    if w:
        time_str = "сейчас" if hour_index == 0 else f"через {hour_index} ч."
        text = (
            f"🌤 **Прогноз ({time_str}):**\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"🌡 Температура: {w['temp']}°C (ощущается как {w['app_temp']}°C)\n"
            f"💧 Влажность: {w['hum']}% | Точка росы: {w['dew']}°C\n"
            f"💨 Ветер: {w['wind']} км/ч\n"
            f"🔽 Давление: {w['pres']} мм рт.ст.\n"
            f"👁 Видимость: {w['vis']} м\n"
            f"🌱 Темп. почвы (6см): {w['soil']}°C\n"
            f"🌧 Осадки: {w['rain']} мм"
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    else:
        bot.answer_callback_query(call.id, "Ошибка получения данных")


@bot.message_handler(commands=['checksens'])
def checksens_handler(m):
    msg = bot.send_message(m.chat.id, "Введите ID любого сенсора для мгновенной проверки:")
    bot.register_next_step_handler(msg, process_check_step)

def process_check_step(message):
    try:
        s_id = int(message.text)
        with sqlite3.connect(DB_FILE) as conn:
            res = conn.execute('SELECT t, h FROM measurements WHERE id = ?', (s_id,)).fetchone()
        
        if res:
            bot.send_message(message.chat.id, f"📊 Сенсор {s_id}:\n🌡 {res[0]}°C\n💧 {res[1]}%")
        else:
            bot.send_message(message.chat.id, "🔍 В базе пока нет данных для этого ID.")
    except:
        bot.send_message(message.chat.id, "Некорректный формат ID.")

if __name__ == '__main__':
    init_db()
    
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=25580, use_reloader=False))
    flask_thread.daemon = True
    flask_thread.start()
    
    bot.polling(none_stop=True)
