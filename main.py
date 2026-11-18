import threading
from http.server import BaseHTTPRequestHandler, HTTPServer import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8900786771"))
CARD = "4413 5976 0750 7256"
CARD_NAME = "Rafikov U."
PRICE = "10 000 so'm"

bot = telebot.TeleBot(TOKEN)

users = {}  # user_id -> dict
pending = {}  # user_id -> dict (to'lov kutayotgan)
approved = {}  # user_id -> dict

def main_menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add(KeyboardButton("📝 Ro'yhatdan o'tish"))
    m.add(KeyboardButton("👀 Anketalarni ko'rish"))
    return m

def gender_menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    m.add(KeyboardButton("Erkak"), KeyboardButton("Ayol"))
    return m

def admin_menu(uid):
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add(KeyboardButton(f"✅ Tasdiqlash {uid}"))
    m.add(KeyboardButton(f"❌ Rad etish {uid}"))
    return m

@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(msg.chat.id,
        "Assalomu alaykum! Oyila botiga xush kelibsiz 💛\n"
        "Bu yerda jiddiy munosabat uchun insonlar tanishadi.\n"
        "Iltimos, bir-birimizga hurmatli bo'laylik.\n\n"
        "Boshlash uchun pastdan tanlang:",
        reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📝 Ro'yhatdan o'tish")
def reg_start(msg):
    uid = msg.from_user.id
    if uid in approved:
        bot.send_message(msg.chat.id, "Siz allaqachon ro'yhatdan o'tgansiz ✅")
        return
    users[uid] = {"step": "name"}
    bot.send_message(msg.chat.id, "Ismingizni yozing (familiya majburiy emas):")

@bot.message_handler(func=lambda m: m.text == "👀 Anketalarni ko'rish")
def show_profiles(msg):
    uid = msg.from_user.id
    if uid not in approved:
        bot.send_message(msg.chat.id, "Anketalarni ko'rish uchun avval ro'yhatdan o'tib, to'lovni tasdiqlatishingiz kerak.\n\n📝 Ro'yhatdan o'tish ni bosing.")
        return
    if not approved:
        bot.send_message(msg.chat.id, "Hozircha tasdiqlangan anketa yo'q.")
        return
    for pid, p in approved.items():
        if pid == uid:
            continue
        text = f"👤 {p['name']}\n🎂 {p['age']} yosh\n⚧ {p['gender']}\n📍 {p['city']}\n💬 {p['about']}"
        try:
            if p.get("photo"):
                bot.send_photo(msg.chat.id, p["photo"], caption=text)
            else:
                bot.send_message(msg.chat.id, text)
        except Exception:
            bot.send_message(msg.chat.id, text)
    bot.send_message(msg.chat.id, "Shu — hozircha barcha anketalar shu. ✅", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text and m.text.startswith("✅ Tasdiqlash"))
def admin_approve(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        uid = int(msg.text.split()[-1])
    except:
        return
    if uid in pending:
        approved[uid] = pending.pop(uid)
        bot.send_message(msg.chat.id, f"✅ {uid} tasdiqlandi!")
        bot.send_message(uid, "Tabriklaymiz! 🎉 To'lovingiz tasdiqlandi.\nEndi anketalarni ko'rishingiz mumkin.", reply_markup=main_menu())
    else:
        bot.send_message(msg.chat.id, "Bu foydalanuvchi kutilayotganlar orasida yo'q.")

@bot.message_handler(func=lambda m: m.text and m.text.startswith("❌ Rad etish"))
def admin_reject(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        uid = int(msg.text.split()[-1])
    except:
        return
    if uid in pending:
        pending.pop(uid)
        bot.send_message(msg.chat.id, f"❌ {uid} rad etildi.")
        bot.send_message(uid, "Afsus, to'lovingiz tasdiqlanmadi. Admin bilan bog'laning.")

@bot.message_handler(content_types=['photo'])
def get_photo(msg):
    uid = msg.from_user.id
    if uid not in users or users[uid].get("step") != "photo":
        return
    users[uid]["photo"] = msg.photo[-1].file_id
    users[uid]["step"] = "done"
    pending[uid] = users.pop(uid)
    bot.send_message(msg.chat.id,
        f"Rahmat! Anketa qabul qilindi. ✅\n\n"
        f"Endi to'lov qiling:\n"
        f"💳 Karta: {CARD}\n"
        f"👤 {CARD_NAME}\n"
        f"💰 Summa: {PRICE}\n\n"
        f"To'lov qilganingizdan so'ng chekni shu yerga yuboring. Admin tekshirib tasdiqlaydi.")
    # Adminga xabar
    p = pending[uid]
    bot.send_message(ADMIN_ID,
        f"🆕 Yangi anketa!\n\n👤 {p['name']}\n🎂 {p['age']}\n⚧ {p['gender']}\n📍 {p['city']}\n💬 {p['about']}\nID: {uid}",
        reply_markup=admin_menu(uid))
    if p.get("photo"):
        try:
            bot.send_photo(ADMIN_ID, p["photo"])
        except:
            pass

@bot.message_handler(content_types=['photo', 'document'])
def get_check(msg):
    uid = msg.from_user.id
    if uid in pending:
        bot.send_message(msg.chat.id, "Chek qabul qilindi ✅ Admin tekshirib tasdiqlaydi. Biroz kuting.")
        # Adminga chekni uzatish
        try:
            if msg.content_type == 'photo':
                bot.send_photo(ADMIN_ID, msg.photo[-1].file_id, caption=f"🧾 Chek — ID: {uid}", reply_markup=admin_menu(uid))
            else:
                bot.send_document(ADMIN_ID, msg.document.file_id, caption=f"🧾 Chek — ID: {uid}", reply_markup=admin_menu(uid))
        except Exception as e:
            print("check forward error", e)

@bot.message_handler(func=lambda m: True)
def steps(msg):
    uid = msg.from_user.id
    if uid not in users:
        return
    step = users[uid].get("step")
    txt = (msg.text or "").strip()
    if step == "name":
        if not txt:
            return
        users[uid]["name"] = txt
        users[uid]["step"] = "age"
        bot.send_message(msg.chat.id, "Yoshingizni yozing (faqat 18+):")
    elif step == "age":
        if not txt.isdigit() or int(txt) < 18:
            bot.send_message(msg.chat.id, "Iltimos, 18 dan katta yosh yozing:")
            return
        users[uid]["age"] = txt
        users[uid]["step"] = "gender"
        bot.send_message(msg.chat.id, "Jinsingizni tanlang:", reply_markup=gender_menu())
    elif step == "gender":
        if txt not in ("Erkak", "Ayol"):
            bot.send_message(msg.chat.id, "Iltimos, tugmadan tanlang: Erkak / Ayol", reply_markup=gender_menu())
            return
        users[uid]["gender"] = txt
        users[uid]["step"] = "city"
        bot.send_message(msg.chat.id, "Qaysi shahardansiz? Masalan: Toshkent")
    elif step == "city":
        users[uid]["city"] = txt
        users[uid]["step"] = "about"
        bot.send_message(msg.chat.id, "O'zingiz haqida 2-3 gapda yozing:")
    elif step == "about":
        users[uid]["about"] = txt
        users[uid]["step"] = "photo"
        bot.send_message(msg.chat.id, "Endi 1 ta rasmingizni yuboring")

class _H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *a):
        pass

def _keep():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), _H).serve_forever()
if __name__ == "__main__":
    print("Oyila bot ishga tushdi...")
    threading.Thread(target=_keep, daemon=True).start()`
    bot.infinity_polling()
