import telebot
import sqlite3
from telebot import types
import time

# Токен вашего бота
API_TOKEN = '8311540508:AAGIhxpSt_YvF5DB7K5uW5gaZQHHoDj4d2k'

# Инициализация бота
bot = telebot.TeleBot(API_TOKEN)

# Функция для безопасного редактирования сообщений
def safe_edit_message_text(call, new_text, new_markup, parse_mode="HTML"):
    """Безопасное редактирование сообщения с проверкой на изменения"""
    try:
        if call.message.text != new_text:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=new_text,
                parse_mode=parse_mode,
                reply_markup=new_markup
            )
        else:
            bot.answer_callback_query(call.id, "Вы уже находитесь в этом разделе")
    except Exception as e:
        if "message is not modified" in str(e):
            bot.answer_callback_query(call.id, "Вы уже находитесь в этом разделе")
        else:
            print(f"Ошибка: {e}")

# ========== БАЗА ДАННЫХ ==========
def init_db():
    conn = sqlite3.connect('atomy_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            referrer_id INTEGER DEFAULT NULL,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def is_bot_owner(user_id):
    owner_info = get_bot_owner()
    return owner_info['user_id'] == user_id

def get_all_users():
    conn = sqlite3.connect('atomy_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, username, full_name, 
               (SELECT COUNT(*) FROM users u2 WHERE u2.referrer_id = users.user_id) as ref_count,
               join_date
        FROM users 
        ORDER BY join_date DESC
    ''')
    users = cursor.fetchall()
    conn.close()
    return users

def get_bot_owner():
    conn = sqlite3.connect('atomy_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, full_name FROM users ORDER BY join_date ASC LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    
    if result:
        user_id, username, full_name = result
        if username:
            return {"user_id": user_id, "username": f"@{username}", "full_name": full_name}
        else:
            return {"user_id": user_id, "username": f"ID: {user_id}", "full_name": full_name}
    return {"user_id": None, "username": "@username_владельца", "full_name": "Владелец бота"}

def get_referrer_info(referrer_id):
    if not referrer_id:
        return get_bot_owner()
    
    conn = sqlite3.connect('atomy_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, full_name FROM users WHERE user_id = ?', (referrer_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        user_id, username, full_name = result
        if username:
            return {"user_id": user_id, "username": f"@{username}", "full_name": full_name}
        else:
            return {"user_id": user_id, "username": f"ID: {user_id}", "full_name": full_name}
    return get_bot_owner()

def add_user(user_id, username, full_name, referrer_id=None):
    conn = sqlite3.connect('atomy_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, full_name, referrer_id)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, full_name, referrer_id))
    conn.commit()
    conn.close()

def get_ref_count(user_id):
    conn = sqlite3.connect('atomy_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users WHERE referrer_id = ?', (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

# ========== КЛАВИАТУРЫ ==========
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("Расскажи мне о компании Atomy")
    btn2 = types.KeyboardButton("Расскажи мне о бизнесе Atomy")
    btn3 = types.KeyboardButton("О продукции компании")
    btn4 = types.KeyboardButton("О системе продвижения в бизнесе")
    markup.add(btn1, btn2, btn3, btn4)
    return markup

def get_company_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("Почему именно Atomy?", callback_data="why_atomy")
    btn2 = types.InlineKeyboardButton("Главное меню", callback_data="main_menu")
    markup.add(btn1, btn2)
    return markup

def get_back_to_menu_keyboard():
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("Главное меню", callback_data="main_menu")
    markup.add(btn)
    return markup

# ========== ОБРАБОТЧИКИ ==========
@bot.message_handler(commands=['start', 'help'])
def cmd_start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.first_name
    if message.from_user.last_name:
        full_name += " " + message.from_user.last_name

    referrer_id = None
    if len(message.text.split()) > 1:
        try:
            referrer_id = int(message.text.split()[1])
        except ValueError:
            referrer_id = None

    add_user(user_id, username, full_name, referrer_id)
    
    contact_info = get_referrer_info(referrer_id) if referrer_id else get_bot_owner()

    welcome_text = f"""Привет! Я ваш гид в мир Atomy — премиального корейского бренда, где качество доступно каждому.

Расскажу, в чём уникальность компании, познакомлю с ассортиментом и объясню, как можно покупать выгодно. А ещё — как начать получать доход, рекомендуя эти продукты другим.

И, при желании, познакомлю Вас с персональным консультантом, который ответит на все Ваши вопросы и поможет подобрать оптимальный для Вас заказ.

📲 Контакт для связи: 
👉 {contact_info['username']} 👈
👤 {contact_info['full_name']}

Выбирайте с чего мне начать рассказывать вам:
⬇️⬇️⬇️"""

    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_keyboard())

    if referrer_id and referrer_id != user_id:
        try:
            referrer_info = f"{full_name} (@{username})" if username else full_name
            notification_text = f"🔔 Новый участник!\nПо вашей ссылке зарегистрировался(ась) {referrer_info}.\nПоздравляем! 🎉"
            bot.send_message(referrer_id, notification_text)
            ref_count = get_ref_count(referrer_id)
            bot.send_message(referrer_id, f"📊 Всего по вашим ссылкам зарегистрировано: {ref_count} человек(а)")
        except:
            pass

# ========== РАЗДЕЛ "О КОМПАНИИ ATOMY" ==========
@bot.message_handler(func=lambda message: message.text == "Расскажи мне о компании Atomy")
def about_company(message):
    company_text = """<b>Atomy (Атоми)</b> - Южно-Корейская компания, прославившаяся натуральными и безопасными продуктами для здоровья. 

Компания Атоми легально работает с 2009 года и пользуется популярностью в Японии, США, Канаде, Мексике и странах Юго-Восточной Азии. А с 12 декабря 2018 года открыта и в России. 

Распространение премиум продукции повседневного спроса идет путем сетевого маркетинга через интернет-магазин компании."""
    
    bot.send_message(message.chat.id, company_text, parse_mode="HTML", reply_markup=get_company_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "why_atomy")
def why_atomy_callback(call):
    why_atomy_text = """В компании Atomy развита стратегия Masstige - массовость и престиж.

Наш девиз: <b>"Абсолютное качество - абсолютная цена"</b>
Мы используем глобальные ресурсы для глобальных продаж и постоянно расширяем свою линейку.

🔸<b>Приверженность принципам</b>
Atomy соблюдает основополагающие столпы структурного бизнеса и всегда держит сказанное слово.

🔸<b>Культура совместного роста</b>
Атоми помогает фирмам-партнерам производить лучшее.

🔸<b>Взаимопомощь всех консультантов</b>

🔸<b>Значительная важность придается достижению успеха каждым участником</b>

🔶«Огромный потенциал – это та компания, сотрудники и клиенты которой счастливы, успешны, которая вносит большой вклад в общество.» - Пак Хан Гиль, председатель Atomy."""
    
    safe_edit_message_text(call, why_atomy_text, get_back_to_menu_keyboard(), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def main_menu_callback(call):
    menu_text = "Возвращаемся в главное меню! Выберите интересующий раздел:"
    bot.send_message(call.message.chat.id, menu_text, reply_markup=get_main_keyboard())
    bot.delete_message(call.message.chat.id, call.message.message_id)

# ========== РАЗДЕЛ "О БИЗНЕСЕ ATOMY" ==========
@bot.message_handler(func=lambda message: message.text == "Расскажи мне о бизнесе Atomy")
def about_business(message):
    business_text = """🔹Бизнес с "Atomy" - прекрасный шанс начать с нуля и добиваться высот, о которых прежде не мог и мечтать.

😃Начать бизнес можно без опыта сетевого маркетинга.

➡️По средней статистике, в нашей компании на первый Мастерский ранг самые простые люди выходят за год – полтора, а это доход уже от 100тыс руб и выше.

✔️ У нас нет обязательных ежемесячных закупок
✔️ У нас нет необходимости заниматься продажами и что-то кому-то навязывать
✔️ У нас не обнуляются баллы - личные вообще никогда, а групповые пока за них не получишь доход!
✔️ Команду строим вместе!
Что это значит? Вышестоящие спонсоры своих новичков будут отдавать в вашу структуру.

✔️ Доход получаем со всей глубины, независимо от того кто пригласил человека – Вы, спонсор или новичок в структуре.

💎Присоединяйтесь к нашей команде!
💡Мы всегда готовы помочь!
😍Поделиться знаниями и научить необходимым навыкам!"""

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("За что и сколько платит компания?", callback_data="salary_info")
    btn2 = types.InlineKeyboardButton("Главное меню", callback_data="main_menu")
    markup.add(btn1, btn2)
    
    bot.send_message(message.chat.id, business_text, reply_markup=markup)

# ========== РАЗДЕЛ "ЗА ЧТО И СКОЛЬКО ПЛАТИТ КОМПАНИЯ?" ==========
@bot.callback_query_handler(func=lambda call: call.data == "salary_info")
def salary_info_callback(call):
    salary_text = """✅Отлично!

😎Давай знакомиться с маркетингом!

😇Как тебе будет удобнее, что бы я рассказал тебе все сам или небольшое видео с разбором маркетинга?"""

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("Посмотреть видео", callback_data="watch_video")
    btn2 = types.InlineKeyboardButton("Давай ты мне расскажешь", callback_data="tell_me")
    btn3 = types.InlineKeyboardButton("Главное меню", callback_data="main_menu")
    markup.add(btn1, btn2, btn3)
    
    safe_edit_message_text(call, salary_text, markup)

# ========== РАЗДЕЛ "ПОСМОТРЕТЬ ВИДЕО" ==========
@bot.callback_query_handler(func=lambda call: call.data == "watch_video")
def watch_video_callback(call):
    video_text = """Знаешь, я еще не видел ни одного человека, который бы понял систему начислений (маркетинг-план) с первого раза.

⚡️В двух словах могу сказать, что в Атоми можно зарабатывать от 1200 рублей в месяц до 200 000 рублей в день.

☝️Самое важное - когда ты начнешь получать 1200 рублей, дальнейший рост твоего дохода невозможно остановить.

⚖️Компания Атоми создала схему сотрудничества, выгодную всем.

Смотри видео и оцени масштаб идеи!

https://vkvideo.ru/video562800842_456239019?list=ln-KRzi3J6nYZtZBCYAVt

Как тебе такие варианты доходов?

Понятное и полное объяснение?"""

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("Мне все понятно. Хочу стать партнером", callback_data="become_partner")
    btn2 = types.InlineKeyboardButton("Шаг назад", callback_data="salary_info")
    btn3 = types.InlineKeyboardButton("Главное меню", callback_data="main_menu")
    markup.add(btn1, btn2, btn3)
    
    safe_edit_message_text(call, video_text, markup)

# ========== РАЗДЕЛ "ХОЧУ СТАТЬ ПАРТНЕРОМ" ==========
@bot.callback_query_handler(func=lambda call: call.data == "become_partner")
def become_partner_callback(call):
    user_id = call.from_user.id
    
    conn = sqlite3.connect('atomy_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT referrer_id FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    referrer_id = result[0] if result else None
    conn.close()
    
    contact_info = get_referrer_info(referrer_id) if referrer_id else get_bot_owner()
    
    partner_text = f"""😎Отлично!

Для регистрации в компании Atomy напишите напрямую:

👉 {contact_info['username']} 👈
👤 {contact_info['full_name']}

Он(а) поможет вам правильно начать бизнес и достичь отличных результатов!

💟 Приятного сотрудничества!

Для возврата в меню нажмите кнопку ниже:"""

    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("Главное меню", callback_data="main_menu")
    markup.add(btn)
    
    safe_edit_message_text(call, partner_text, markup)

# ========== РАЗДЕЛ "ДАВАЙ ТЫ МНЕ РАССКАЖЕШЬ" ==========
@bot.callback_query_handler(func=lambda call: call.data == "tell_me")
def tell_me_callback(call):
    tell_me_text = """😇С превеликим удовольствием!

Здесь я тебе подробно расскажу обо всех ступеньках в маркетинге, какие бонусы ждут тебя на каждом этапе и объясню как перейти на следующий уровень.

Для начала объясню тебе что такое PV.

<b>PV (Point Value)</b> - это баллы, которые начисляются за покупку продукции Atomy.
Есть личные PV, которые ты получаешь за покупку продукции для себя. А есть групповые PV, которые начисляются за покупку других людей в одной из твоих веток.

Теперь, когда мы разобрались в терминологии, я могу рассказать тебе обо всем подробнее.

⬇️⬇️⬇️⬇️⬇️"""

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("📋 Классификация и условия дистрибьюторства", callback_data="classification")
    btn2 = types.InlineKeyboardButton("💰 Спонсорское вознаграждение", callback_data="sponsor_reward")
    btn3 = types.InlineKeyboardButton("🏆 Мастерское вознаграждение", callback_data="master_reward")
    btn4 = types.InlineKeyboardButton("📈 Условия повышения уровня мастерства", callback_data="master_level")
    btn5 = types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    
    safe_edit_message_text(call, tell_me_text, markup, parse_mode="HTML")

# ========== КЛАССИФИКАЦИЯ И УСЛОВИЯ ДИСТРИБЬЮТОРСТВА ==========
@bot.callback_query_handler(func=lambda call: call.data == "classification")
def classification_callback(call):
    text = """🔶<b>Классификация и условия дистрибьюторства</b>🔶

Ниже я расположил ступени по мере возрастания товарооборота в твоей структуре.

Посмотри какой рост может быть уже в первый месяц, два, три в твоем бизнесе!"""

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("🛒 Торговый представитель", callback_data="sales_rep")
    btn2 = types.InlineKeyboardButton("🤝 Агент", callback_data="agent")
    btn3 = types.InlineKeyboardButton("⭐ Специальный агент", callback_data="special_agent")
    btn4 = types.InlineKeyboardButton("🚗 Дилер", callback_data="dealer")
    btn5 = types.InlineKeyboardButton("💎 Эксклюзивный представитель", callback_data="exclusive_rep")
    btn6 = types.InlineKeyboardButton("◀️ Назад к списку", callback_data="tell_me")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    
    safe_edit_message_text(call, text, markup, parse_mode="HTML")

# ========== ТОРГОВЫЙ ПРЕДСТАВИТЕЛЬ ==========
@bot.callback_query_handler(func=lambda call: call.data == "sales_rep")
def sales_rep_callback(call):
    text = """🛒 <b>Торговый представитель</b>

🔶Торговый представитель 🔶

💎Эта самая первая ступень твоего пути!
💡Когда твои личные PV составляют от 10 000 PV до 299 999 PV (это от 1400 до 40000 руб), а групповой оборот меньшей ветки накопится до 300 000 PV, складывается бинарный шаг(степ), за который ты получаешь доход.
💸Твой Чек за каждый бинарный шаг составит около 1250руб.

💰Бинарные шаги могут проходить ежедневно!"""

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton("◀️ Назад", callback_data="classification")
    btn_masters = types.InlineKeyboardButton("🔹 Квалификация мастеров", callback_data="master_qualification")
    btn_menu = types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    markup.add(btn_back, btn_masters, btn_menu)
    
    safe_edit_message_text(call, text, markup, parse_mode="HTML")

# ========== АГЕНТ ==========
@bot.callback_query_handler(func=lambda call: call.data == "agent")
def agent_callback(call):
    text = """🤝 <b>Агент</b>

🔶Агент 🔶

💎Это ранг который позволяет получать за бинарный шаг сразу в 3 раза больше!!!

💡Стать Агентом можно при достижении одного из условий:
1 Личные PV >300000
2. Накопление 600000PV в меньшей ветке за предыдущий месяц

💸Твой Чек за КАЖДЫЙ бинарный шаг составит около 3600руб.

💰Напомню, бинарные шаги могут проходить ежедневно!"""

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton("◀️ Назад", callback_data="classification")
    btn_masters = types.InlineKeyboardButton("🔹 Квалификация мастеров", callback_data="master_qualification")
    btn_menu = types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    markup.add(btn_back, btn_masters, btn_menu)
    
    safe_edit_message_text(call, text, markup, parse_mode="HTML")

# ========== СПЕЦИАЛЬНЫЙ АГЕНТ ==========
@bot.callback_query_handler(func=lambda call: call.data == "special_agent")
def special_agent_callback(call):
    text = """⭐ <b>Специальный агент</b>

🔶Специальный агент 🔶

💎Этот статус присваивается при достижении одного из условий:
1. Личные PV >700000
2. Накопление 1400000PV в меньшей ветке за предыдущий месяц
💸Твой Чек за КАЖДЫЙ бинарный шаг составит около 7200 руб."""

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton("◀️ Назад", callback_data="classification")
    btn_masters = types.InlineKeyboardButton("🔹 Квалификация мастеров", callback_data="master_qualification")
    btn_menu = types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    markup.add(btn_back, btn_masters, btn_menu)
    
    safe_edit_message_text(call, text, markup, parse_mode="HTML")

# ========== ДИЛЕР ==========
@bot.callback_query_handler(func=lambda call: call.data == "dealer")
def dealer_callback(call):
    text = """🚗 <b>Дилер</b>

🔶Дилер🔶

💎Этот статус присваивается при достижении одного из условий:
1. Личные PV >1500000
2. Накопление 3000000PV в меньшей ветке за предыдущий месяц

💸Твой Чек за КАЖДЫЙ бинарный шаг составит около 14500 руб."""

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton("◀️ Назад", callback_data="classification")
    btn_masters = types.InlineKeyboardButton("🔹 Квалификация мастеров", callback_data="master_qualification")
    btn_menu = types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    markup.add(btn_back, btn_masters, btn_menu)
    
    safe_edit_message_text(call, text, markup, parse_mode="HTML")

# ========== ЭКСКЛЮЗИВНЫЙ ПРЕДСТАВИТЕЛЬ ==========
@bot.callback_query_handler(func=lambda call: call.data == "exclusive_rep")
def exclusive_rep_callback(call):
    text = """💎 <b>Эксклюзивный представитель</b>

🔶Эксклюзивный дистрибьютор🔶

💎Этот статус присваивается при достижении одного из условий:
1. Личные PV >2400000
2. Накопление 4800000PV в меньшей ветке за предыдущий месяц

💸Твой Чек за КАЖДЫЙ бинарный шаг составит около от 21000 до 72000 руб.

💰Внимание! Бинарный шаг может проходить ежедневно! Все зависит от товарооборота, который будет проходить в вашей структуре"""

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton("◀️ Назад", callback_data="classification")
    btn_masters = types.InlineKeyboardButton("🔹 Квалификация мастеров", callback_data="master_qualification")
    btn_menu = types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    markup.add(btn_back, btn_masters, btn_menu)
    
    safe_edit_message_text(call, text, markup, parse_mode="HTML")

# ========== КВАЛИФИКАЦИЯ МАСТЕРОВ ==========
@bot.callback_query_handler(func=lambda call: call.data == "master_qualification")
def master_qualification_callback(call):
    text = """🔹<b>Мастерское вознаграждение и квалификация мастеров</b>🔹

20% от общего количества PV компании распределяется между участниками согласно их уровням мастерства.

✔️Мастерское вознаграждение выплачивается два раза в месяц на 7-ой день после завершения периода подсчета. 
Период подсчета: с 1 по 15 число месяца, с 16 по конец месяца."""

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("🛍️ Мастер продаж", callback_data="sales_master")
    btn2 = types.InlineKeyboardButton("💎 Бриллиантовый мастер", callback_data="diamond_master")
    btn3 = types.InlineKeyboardButton("🌹 Мастер шаронской розы", callback_data="sharon_master")
    btn4 = types.InlineKeyboardButton("⭐ Стар мастер", callback_data="star_master")
    btn5 = types.InlineKeyboardButton("👑 Роял мастер", callback_data="royal_master")
    btn6 = types.InlineKeyboardButton("🏆 Краун мастер", callback_data="crown_master")
    btn7 = types.InlineKeyboardButton("🌍 Империал мастер", callback_data="imperial_master")
    btn8 = types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8)
    
    safe_edit_message_text(call, text, markup, parse_mode="HTML")

# ========== МАСТЕР ПРОДАЖ ==========
@bot.callback_query_handler(func=lambda call: call.data == "sales_master")
def sales_master_callback(call):
    text = """🛍️ <b>Мастер продаж</b>

🔹Поощрения для уровня "Мастер продаж"🔹
Денежное вознаграждение в размере 30 000 руб.💰"""

    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("◀️ Назад", callback_data="master_qualification")
    btn_menu = types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    markup.add(btn_back, btn_menu)
    
    safe_edit_message_text(call, text, markup, parse_mode="HTML")

# ========== БРИЛЛИАНТОВЫЙ МАСТЕР ==========
@bot.callback_query_handler(func=lambda call: call.data == "diamond_master")
def diamond_master_callback(call):
    text = """💎 <b>Бриллиантовый мастер</b>

🔹Поощрения для уровня "Бриллиантовый мастер"🔹
Денежное вознаграждение в размере 90 000 руб.💰"""

    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("◀️ Назад", callback_data="master_qualification")
    btn_menu = types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    markup.add(btn_back, btn_menu)
    
    safe_edit_message_text(call, text, markup, parse_mode="HTML")

# ========== МАСТЕР ШАРОНСКОЙ РОЗЫ ==========
@bot.callback_query_handler(func=lambda call: call.data == "sharon_master")
def sharon_master_callback(call):
    text = """🌹 <b>Мастер шаронской розы</b>

🔹Поощрения для уровня "Мастер Шаронской Розы"🔹
1️⃣Денежное вознаграждение в размере 125 000 руб.💰💰💰
2️⃣Поездка на двоих на 3 суток (можно взять с собой только близкого родственника)👨‍👦👩‍👧✈️"""

    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("◀️ Назад", callback_data="master_qualification")
    btn_menu = types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    markup.add(btn_back, btn_menu)
    
    safe_edit_message_text(call, text, markup, parse_mode="HTML")

# ========== СТАР МАСТЕР ==========
@bot.callback_query_handler(func=lambda call: call.data == "star_master")
def star_master_callback(call):
    text = """⭐ <b>Стар мастер</b>

🔹Поощрения для уровня "Стар мастер"🔹
1️⃣денежное вознаграждение в размере 625 000 руб.💰💰💰
2️⃣поездка на четверых на 3 суток (можно взять с собой только близких родственников)👨‍👦👫 ✈️"""

    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("◀️ Назад", callback_data="master_qualification")
    btn_menu = types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    markup.add(btn_back, btn_menu)
    
    safe_edit_message_text(call, text, markup, parse_mode="HTML")

# ========== РОЯЛ МАСТЕР ==========
@bot.callback_query_handler(func=lambda call: call.data == "royal_master")
def royal_master_callback(call):
    text = """👑 <b>Роял мастер</b>

🔹Поощрения для уровня "Роял мастер"🔹
1️⃣денежное вознаграждение в размере 3 125 000 руб. 💰💰💰 
2️⃣поездка на четверых на 10 суток (можно взять с собой только близких родственников) 👨‍👦👫 ✈️
3️⃣За каждый период достижения:
дополнительное денежное вознаграждение в размере 62 500 руб.💳                                    
бесплатная аренда седана бизнес класса🚘"""

    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("◀️ Назад", callback_data="master_qualification")
    btn_menu = types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    markup.add(btn_back, btn_menu)
    
    safe_edit_message_text(call, text, markup, parse_mode="HTML")

# ========== КРАУН МАСТЕР ==========
@bot.callback_query_handler(func=lambda call: call.data == "crown_master")
def crown_master_callback(call):
    text = """🏆 <b>Краун мастер</b>

🔹Поощрения для уровня "Краун мастер"🔹

1️⃣поездка на четверых на 10 суток (можно взять с собой только близких родственников)👩‍👦👨‍👦
2️⃣машина класса Люкс 🚘 
3️⃣денежное вознаграждение в размере 18 750 000 руб.💰💰💰
4️⃣За каждый период достижения:
дополнительное денежное вознаграждение в размере 156 250 руб.💳"""

    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("◀️ Назад", callback_data="master_qualification")
    btn_menu = types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    markup.add(btn_back, btn_menu)
    
    safe_edit_message_text(call, text, markup, parse_mode="HTML")

# ========== ИМПЕРИАЛ МАСТЕР ==========
@bot.callback_query_handler(func=lambda call: call.data == "imperial_master")
def imperial_master_callback(call):
    text = """🌍 <b>Империал мастер</b>

🔹Поощрения для уровня "Империал мастер"🔹

1️⃣поездка на четверых на 10 суток (можно взять с собой только близких родственников)👨‍👦👩‍👧✈️
2️⃣машина класса люкс🚘 
За каждый период достижения:
3️⃣дополнительное денежное вознаграждение в размере 312 500 руб.💳
4️⃣бесплатная аренда офиса площадью 170 м2 🏢
5️⃣личный ассистент 👩‍💼
6️⃣денежное вознаграждение в размере 62 500 000 руб. 💰💰💰"""

    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("◀️ Назад", callback_data="master_qualification")
    btn_menu = types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    markup.add(btn_back, btn_menu)
    
    safe_edit_message_text(call, text, markup, parse_mode="HTML")

# ========== СПОНСОРСКОЕ ВОЗНАГРАЖДЕНИЕ ==========
@bot.callback_query_handler(func=lambda call: call.data == "sponsor_reward")
def sponsor_reward_callback(call):
    text = """💰 <b>Спонсорское вознаграждение</b>

🔶Спонсорское вознаграждение🔶

44% PV от общего количества PV компании распределяется между участниками согласно их уровням дистрибьюторства.

🔹Вознаграждение за количество PV, накопленные в период со среды до вторника. Выплачивается на следующей неделе после завершения периода подсчета.

🔹Дистрибьютор начинает накапливать групповые PV только после накопления 10 000 личных PV."""

    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("◀️ Назад", callback_data="tell_me")
    btn_menu = types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    markup.add(btn_back, btn_menu)
    
    safe_edit_message_text(call, text, markup, parse_mode="HTML")

# ========== МАСТЕРСКОЕ ВОЗНАГРАЖДЕНИЕ ==========
@bot.callback_query_handler(func=lambda call: call.data == "master_reward")
def master_reward_callback(call):
    """Перенаправление на раздел квалификации мастеров"""
    master_qualification_callback(call)

# ========== УСЛОВИЯ ПОВЫШЕНИЯ УРОВНЯ МАСТЕРСТВА ==========
@bot.callback_query_handler(func=lambda call: call.data == "master_level")
def master_level_callback(call):
    text = """📈 <b>Условия повышения уровня мастерства</b>

🔹Условия повышения уровня🔹

Отсутствуют для уровней:
Мастер продаж
Бриллиантовый мастер
Мастер Шаронской Розы

Условия для уровней Стар мастер, Роял мастер, Краун мастер, Империал мастер - получить текущий уровень 3 раза."""

    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("◀️ Назад", callback_data="tell_me")
    btn_menu = types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    markup.add(btn_back, btn_menu)
    
    safe_edit_message_text(call, text, markup, parse_mode="HTML")

# ========== РЕФЕРАЛЬНАЯ СИСТЕМА ==========
@bot.message_handler(commands=['ref', 'рефералка', 'ссылка'])
def cmd_ref(message):
    user_id = message.from_user.id
    if not is_bot_owner(user_id):
        bot.reply_to(message, "⛔ Эта команда доступна только владельцу бота!")
        return
    
    bot_info = bot.get_me()
    bot_username = bot_info.username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    ref_count = get_ref_count(user_id)
    
    bot.send_message(
        message.chat.id,
        f"👑 <b>Ваша реферальная ссылка как владельца:</b>\n\n"
        f"<code>{ref_link}</code>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• Привлечено человек: {ref_count}\n\n"
        f"<i>Отправляйте эту ссылку вашим клиентам и партнерам.</i> 📢",
        parse_mode="HTML"
    )

@bot.message_handler(commands=['users', 'пользователи'])
def cmd_users(message):
    user_id = message.from_user.id
    if not is_bot_owner(user_id):
        bot.reply_to(message, "⛔ Эта команда доступна только владельцу бота!")
        return
    
    users = get_all_users()
    if not users:
        bot.reply_to(message, "📭 В базе данных пока нет пользователей.")
        return
    
    users_text = "👥 <b>Список пользователей:</b>\n\n"
    for i, (uid, username, full_name, ref_count, join_date) in enumerate(users[:50], 1):
        user_ref = f"ID: <code>{uid}</code>"
        if username:
            user_ref = f"@{username}"
        users_text += f"{i}. {full_name} ({user_ref})\n"
        users_text += f"   📊 Рефералов: {ref_count}\n"
        users_text += f"   📅 Дата: {join_date[:10]}\n\n"
    
    if len(users) > 50:
        users_text += f"\n... и еще {len(users) - 50} пользователей"
    
    bot.send_message(message.chat.id, users_text, parse_mode="HTML")

@bot.message_handler(commands=['generate', 'генерация'])
def cmd_generate(message):
    user_id = message.from_user.id
    if not is_bot_owner(user_id):
        bot.reply_to(message, "⛔ Эта команда доступна только владельцу бота!")
        return
    
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message,
                     "❓ <b>Использование:</b>\n"
                     "<code>/generate ID_пользователя</code>\n\n"
                     "Пример: <code>/generate 123456789</code>\n\n"
                     "Чтобы получить ID пользователя, используйте команду /users",
                     parse_mode="HTML")
        return
    
    try:
        target_user_id = int(args[1])
    except ValueError:
        bot.reply_to(message, "❌ Неверный ID пользователя!")
        return
    
    conn = sqlite3.connect('atomy_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, full_name FROM users WHERE user_id = ?', (target_user_id,))
    user_data = cursor.fetchone()
    conn.close()
    
    if not user_data:
        bot.reply_to(message, f"❌ Пользователь с ID {target_user_id} не найден!")
        return
    
    target_username, target_full_name = user_data
    bot_info = bot.get_me()
    bot_username = bot_info.username
    ref_link = f"https://t.me/{bot_username}?start={target_user_id}"
    ref_count = get_ref_count(target_user_id)
    
    response = f"""✅ <b>Реферальная ссылка создана!</b>

👤 <b>Для пользователя:</b>
• Имя: {target_full_name}
• Username: @{target_username if target_username else 'отсутствует'}
• ID: <code>{target_user_id}</code>

🔗 <b>Реферальная ссылка:</b>
<code>{ref_link}</code>

📊 <b>Статистика пользователя:</b>
• Привлечено человек: {ref_count}

<i>Отправьте эту ссылку пользователю.</i>"""
    
    bot.send_message(message.chat.id, response, parse_mode="HTML")

@bot.message_handler(commands=['stats', 'статистика'])
def cmd_stats(message):
    user_id = message.from_user.id
    ref_count = get_ref_count(user_id)
    owner_status = "👑 <b>Вы владелец этого бота!</b>\n\n" if is_bot_owner(user_id) else ""
    
    bot.send_message(
        message.chat.id,
        f"{owner_status}"
        f"📊 <b>Ваша статистика:</b>\n\n"
        f"• Привлечено человек: {ref_count}\n"
        f"• Ваш ID: <code>{user_id}</code>\n\n"
        f"<i>Для регистрации новых участников используйте ссылки от владельца бота.</i>",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )

# ========== РАЗДЕЛ "О ПРОДУКЦИИ КОМПАНИИ" ==========
@bot.message_handler(func=lambda message: message.text == "О продукции компании")
def about_products(message):
    products_text = """Я с радостью расскажу о нашей продукции! 😉

💡Продукция компании Атоми сертифицирована по международным стандартам GMP и HACCP, что обеспечивает использование лучшего сырья с соблюдением высоких требований технологического процесса и контроль на всех этапах производства.

Выбери ниже, что тебе интересно и я тебе расскажу! ⬇️"""

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("💊 Здоровье", callback_data="health")
    btn2 = types.InlineKeyboardButton("💇‍♀️ Уход за волосами", callback_data="hair_care")
    btn3 = types.InlineKeyboardButton("🧴 Уход за кожей", callback_data="skin_care")
    btn4 = types.InlineKeyboardButton("🦷 Уход за полостью рта", callback_data="oral_care")
    btn5 = types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    
    bot.send_message(message.chat.id, products_text, reply_markup=markup)

# ========== ЗДОРОВЬЕ ==========
@bot.callback_query_handler(func=lambda call: call.data == "health")
def health_callback(call):
    text = """💊 <b>Продукция для здоровья</b>

✅Здоровье с Atomy

Товары для здоровья Южнокорейской Компании Атоми для всех категорий населения и все возрастных групп. Здоровый образ жизни возведен жителями Южной Кореи в культ. Неудивительно, что товары, имеющие к нему непосредственное отношение, произведены по высочайшим стандартам качества. Натуральные средства от компании Atomy для здоровья и красоты.

✅Атоми красный женьшень
✅Аляска Е-Омега 3
✅Атоми Омега 3 для детей
✅Чай для похудения, Атоми Puer Tea
✅Атоми Color Food Мульти витамины
✅Атоми Софора квин
✅Спирулина Атоми

😇Я хотел сделать короткое описание продукции, но ее ассортимент поистине огромен!

Каталог: https://www.atomy.ru/category?dispCtgNo=2411002249&sortType=POPULAR  
https://kr.atomy.com/category?dispCtgNo=2412002654&sortType=POPULAR
Сертификаты: https://ch.atomy.com/ru/categories/58"""

    user_id = call.from_user.id
    conn = sqlite3.connect('atomy_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT referrer_id FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    referrer_id = result[0] if result else None
    conn.close()
    
    contact_info = get_referrer_info(referrer_id) if referrer_id else get_bot_owner()
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_order = types.InlineKeyboardButton("🛒 Хочу заказать", callback_data=f"order_{contact_info['user_id']}")
    btn_back = types.InlineKeyboardButton("◀️ Назад к продукции", callback_data="back_to_products")
    btn_menu = types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    markup.add(btn_order, btn_back, btn_menu)
    
    safe_edit_message_text(call, text, markup, parse_mode="HTML")

# ========== УХОД ЗА ВОЛОСАМИ ==========
@bot.callback_query_handler(func=lambda call: call.data == "hair_care")
def hair_care_callback(call):
    text = """💇‍♀️ <b>Уход за волосами</b>

✅Уход за волосами с Atomy

Atomy — это средства для принятия ванны и душа, а также средства по уходу за волосами, лицом и телом, разработанные специально для всех типов кожи. Натуральные активные компоненты, входящие в средства по уходу за волосами, активно воздействуют на кожу головы и волос, обеспечивая необходимую микроциркуляцию для питания волос изнутри.

Для того чтобы хорошо выглядеть, необходима специальная качественная косметика для комплексного ухода за кожей лица, волосами и телом. Комплексные средства по уходу за волосами позволяют предупредить преждевременное старение волос, их выпадение.

Оригинальные органические компоненты, гипоаллергенные свойства, инновационные технологии, разработанные в Южной Корее - это основные качественные преимущества продуктов компании Atomy, позволяющей ей завоёвывать всё новые и новые страны.

Каталог: https://www.atomy.ru/category?dispCtgNo=2504003410&sortType=POPULAR 
https://kr.atomy.com/category?dispCtgNo=2412002657&sortType=POPULAR
Сертификаты: https://ch.atomy.com/ru/categories/59"""

    user_id = call.from_user.id
    conn = sqlite3.connect('atomy_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT referrer_id FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    referrer_id = result[0] if result else None
    conn.close()
    
    contact_info = get_referrer_info(referrer_id) if referrer_id else get_bot_owner()
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_order = types.InlineKeyboardButton("🛒 Хочу заказать", callback_data=f"order_{contact_info['user_id']}")
    btn_back = types.InlineKeyboardButton("◀️ Назад к продукции", callback_data="back_to_products")
    btn_menu = types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    markup.add(btn_order, btn_back, btn_menu)
    
    safe_edit_message_text(call, text, markup, parse_mode="HTML")

# ========== УХОД ЗА КОЖЕЙ ==========
@bot.callback_query_handler(func=lambda call: call.data == "skin_care")
def skin_care_callback(call):
    text = """🧴 <b>Уход за кожей</b>

✅Уход за кожей с Atomy

✅Корейская органическая косметика Atomy разработана только из натуральных компонентов. Гипоаллергенная косметика подходит практически всем. Косметические средства компании Atomy зарекомендовали себя наилучшим образом.

Кожа вокруг глаз особенно чувствительна, поэтому подобрать гипоаллергенный, но при этом эффективный крем — задача не из простых.
Эффективность косметических средств Atomy доказана в ходе клинических исследований под тщательным контролем дерматологов, поэтому вы можете быть уверены, что даже сверхчувствительная кожа отреагирует на нанесение средства благоприятно.

✅Absolute CellActive Skincare - система антивозрастного ухода за кожей
✅Atomy SkinCare 6 system - система ухода за кожей из натуральных компонентов
✅Набор для глубокого увлажнения кожи Atomy Aqua
✅Профессиональный вечерний уход за кожей в домашних условиях Atomy Evening Care 4 Set

https://www.atomy.ru/category?dispCtgNo=2504003386&sortType=POPULAR
https://kr.atomy.com/category?dispCtgNo=2412002678&sortType=POPULAR
Сертификаты:
1️⃣уходовая косметика https://ch.atomy.com/ru/categories/50
2️⃣макияж  https://ch.atomy.com/ru/categories/62 
3️⃣защита от солнца https://ch.atomy.com/ru/categories/64                                                     
4️⃣мужская линия https://ch.atomy.com/ru/categories/65
Подобрать уход за кожей лица прямо сейчас
https://frata.myluuk.app/widget/v2/index.html?vendor=atomy"""

    user_id = call.from_user.id
    conn = sqlite3.connect('atomy_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT referrer_id FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    referrer_id = result[0] if result else None
    conn.close()
    
    contact_info = get_referrer_info(referrer_id) if referrer_id else get_bot_owner()
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_order = types.InlineKeyboardButton("🛒 Хочу заказать", callback_data=f"order_{contact_info['user_id']}")
    btn_back = types.InlineKeyboardButton("◀️ Назад к продукции", callback_data="back_to_products")
    btn_menu = types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    markup.add(btn_order, btn_back, btn_menu)
    
    safe_edit_message_text(call, text, markup, parse_mode="HTML")

# ========== УХОД ЗА ПОЛОСТЬЮ РТА ==========
@bot.callback_query_handler(func=lambda call: call.data == "oral_care")
def oral_care_callback(call):
    text = """🦷 <b>Уход за полостью рта</b>

✅Зубная паста Атоми с прополисом
👉Зубная паста с прополисом является одним из самых продаваемых товаров компании Atomy. Большинство, попробовав ее один раз, возвращаются за ней, и другой продукцией от южно-корейской компании снова и снова.

🔸Основными действующими компонентами являются экстракты зеленого чая и прополиса. Обладают антибактериальными и противовоспалительными свойствами, препятствуют размножению бактерий, предотвращают неприятный запах.

🔸Так же в состав пасты входит такое вещество как ксилит, он предотвращает метаболический процесс бактерий, которые являются причиной появления зубного налета, уменьшает бактериальный слой на поверхности зубов.

💡Обязательный элементом является фтор, который проникает в кристаллическую решетку эмали зуба и укрепляет ее, повышая сопротивляемость к воздействию патогенных микроорганизмов и защищая от образования кариеса, и потери кальция.

⬇️Каталог всего разнообразия ухода за полостью рта⬇️

https://www.atomy.ru/category?dispCtgNo=2504003408&sortType=POPULAR"""

    user_id = call.from_user.id
    conn = sqlite3.connect('atomy_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT referrer_id FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    referrer_id = result[0] if result else None
    conn.close()
    
    contact_info = get_referrer_info(referrer_id) if referrer_id else get_bot_owner()
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_order = types.InlineKeyboardButton("🛒 Хочу заказать", callback_data=f"order_{contact_info['user_id']}")
    btn_back = types.InlineKeyboardButton("◀️ Назад к продукции", callback_data="back_to_products")
    btn_menu = types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    markup.add(btn_order, btn_back, btn_menu)
    
    safe_edit_message_text(call, text, markup, parse_mode="HTML")

# ========== ХОЧУ ЗАКАЗАТЬ ==========
@bot.callback_query_handler(func=lambda call: call.data.startswith("order_"))
def order_callback(call):
    owner_id = int(call.data.split("_")[1])
    owner_info = get_referrer_info(owner_id)
    
    order_text = f"""😍 <b>Отлично!</b>

Для заказа заинтересовавшей вас продукции, напиши моему владельцу напрямую: 

👉 {owner_info['username']} 👈
👤 {owner_info['full_name']}

💟 С тобой очень приятно работать!

👉 Если я могу тебе еще чем-то помочь, то выбирай кнопку "Обратно в меню"!"""

    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("◀️ Обратно в меню", callback_data="back_to_products")
    btn_menu = types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    markup.add(btn_back, btn_menu)
    
    safe_edit_message_text(call, order_text, markup, parse_mode="HTML")

# ========== НАЗАД К ПРОДУКЦИИ ==========
@bot.callback_query_handler(func=lambda call: call.data == "back_to_products")
def back_to_products_callback(call):
    products_text = """Я с радостью расскажу о нашей продукции! 😉

💡Продукция компании Атоми сертифицирована по международным стандартам GMP и HACCP, что обеспечивает использование лучшего сырья с соблюдением высоких требований технологического процесса и контроль на всех этапах производства.

Выбери ниже, что тебе интересно и я тебе расскажу! ⬇️"""

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("💊 Здоровье", callback_data="health")
    btn2 = types.InlineKeyboardButton("💇‍♀️ Уход за волосами", callback_data="hair_care")
    btn3 = types.InlineKeyboardButton("🧴 Уход за кожей", callback_data="skin_care")
    btn4 = types.InlineKeyboardButton("🦷 Уход за полостью рта", callback_data="oral_care")
    btn5 = types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    
    safe_edit_message_text(call, products_text, markup)

# ========== О СИСТЕМЕ ПРОДВИЖЕНИЯ В БИЗНЕСЕ ==========
@bot.message_handler(func=lambda message: message.text == "О системе продвижения в бизнесе")
def about_system(message):
    system_text = """🔶<b>Классификация и условия дистрибьюторства</b>🔶

Ниже я расположил ступени по мере возрастания товарооборота в твоей структуре.

Посмотри какой рост может быть уже в первый месяц, два, три в твоем бизнесе!"""

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("🛒 Торговый представитель", callback_data="sales_rep")
    btn2 = types.InlineKeyboardButton("🤝 Агент", callback_data="agent")
    btn3 = types.InlineKeyboardButton("⭐ Специальный агент", callback_data="special_agent")
    btn4 = types.InlineKeyboardButton("🚗 Дилер", callback_data="dealer")
    btn5 = types.InlineKeyboardButton("💎 Эксклюзивный представитель", callback_data="exclusive_rep")
    btn6 = types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu_from_system")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    
    bot.send_message(message.chat.id, system_text, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "main_menu_from_system")
def main_menu_from_system_callback(call):
    menu_text = "Возвращаемся в главное меню! Выберите интересующий раздел:"
    bot.send_message(call.message.chat.id, menu_text, reply_markup=get_main_keyboard())
    bot.delete_message(call.message.chat.id, call.message.message_id)

# ========== ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ ==========
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if message.text not in ["Расскажи мне о компании Atomy",
                            "Расскажи мне о бизнесе Atomy",
                            "О продукции компании",
                            "О системе продвижения в бизнесе"]:
        bot.reply_to(message, "Я вас не понял. Используйте кнопки меню или команды: /start, /myref, /stats")

@bot.message_handler(commands=['setowner', 'установитьвладельца'])
def cmd_setowner(message):
    user_id = message.from_user.id
    
    conn = sqlite3.connect('atomy_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    conn.close()
    
    if count > 0:
        current_owner = get_bot_owner()
        if user_id != current_owner['user_id']:
            bot.reply_to(message, "⛔ Изменить владельца может только текущий владелец!")
            return
    
    username = message.from_user.username
    full_name = message.from_user.first_name
    if message.from_user.last_name:
        full_name += " " + message.from_user.last_name
    
    conn = sqlite3.connect('atomy_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, username, full_name)
        VALUES (?, ?, ?)
    ''', (user_id, username, full_name))
    conn.commit()
    conn.close()
    
    bot.reply_to(message, f"✅ Вы теперь владелец бота!\nВаш ID: <code>{user_id}</code>", parse_mode="HTML")

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    print("Бот Atomy запущен...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            time.sleep(5)
            continue
