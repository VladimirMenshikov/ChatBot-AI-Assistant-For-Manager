import telebot
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
from keys import api_key, BOT_TOKEN

# Настройка клиента OpenAI
client = OpenAI(
    api_key=api_key,
    base_url="https://api.proxyapi.ru/openai/v1",
)

# Настройка бота Telebot
bot = telebot.TeleBot(BOT_TOKEN)

# Системный промпт
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "Ты — ассистент менеджера по продажам бумаги для плоттера. "
        "Твоя задача — оперативно помогать с составлением коммерческих предложений, "
        "созданием рекламных рассылок, написанием профессиональных ответов на клиентские запросы "
        "и анализом договоров. Ты должен быть точным, лаконичным и следовать деловому стилю, "
        "учитывая специфику бизнеса и потребности клиента.\n\n"
        "Инструкции по стилю:\n"
        "Соблюдай логичную и понятную структуру текста.\n"
        "Будь вежливым и профессиональным.\n"
        "Подчеркивай выгоды для клиента в каждом тексте.\n"
        "Избегай лишней информации и двусмысленности.\n"
        "Пиши от имени генерального директора Смехова Петра Семёновича\n"
        "ООО 'Бумага и втулка', г. СПб, ул. Рентгена, д. 56"
    ),
}

# Хранение истории диалога для каждого пользователя
user_conversations = {}

# Обработчик команды /help
@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = (
        "Доступные команды:\n"
        "/start - начать взаимодействие\n"
        "/help - показать это сообщение помощи\n"
        "/sound - вывести предыдущий ответ голосовым сообщением"
    )
    bot.send_message(message.chat.id, help_text)

# Функция обработки текстовых сообщений
@bot.message_handler(func=lambda message: message.text and not message.text.startswith("/sound"))
def handle_message(message):
    user_id = message.chat.id
    user_message = message.text

    # Инициализация истории диалога для пользователя
    if user_id not in user_conversations:
        user_conversations[user_id] = [SYSTEM_PROMPT]

    # Добавляем сообщение пользователя в историю
    user_conversations[user_id].append({"role": "user", "content": user_message})

    try:
        # Запрос к нейросети
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=user_conversations[user_id]
        )

        # Получение ответа
        ai_response = response.choices[0].message.content

        # Отправляем ответ пользователю
        bot.reply_to(message, ai_response)

        # Добавляем ответ нейросети в историю
        user_conversations[user_id].append({"role": "assistant", "content": ai_response})

    except Exception as e:
        # Обработка ошибок
        bot.reply_to(message, f"Произошла ошибка: {e}")
        print(f"Ошибка: {e}")

# Функция обработки команды /sound
@bot.message_handler(commands=["sound"])
def handle_sound(message):
    user_id = message.chat.id

    # Проверяем, есть ли история сообщений
    if user_id not in user_conversations or len(user_conversations[user_id]) < 2:
        bot.reply_to(message, "Пожалуйста, сначала начните диалог.")
        return

    try:
        # Получаем последний ответ бота из истории
        last_response = user_conversations[user_id][-1]["content"]

        # Генерируем голосовое сообщение с помощью gTTS
        tts = gTTS(text=last_response, lang="ru") 
        voice = BytesIO()
        tts.write_to_fp(voice)
        voice.seek(0)

        # Отправляем голосовое сообщение пользователю
        bot.send_voice(message.chat.id, voice)

    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {e}")
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    print("Бот запущен и готов к работе.")
    bot.infinity_polling()