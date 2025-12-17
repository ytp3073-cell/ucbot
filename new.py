import json, os, uuid, re
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ================= CONFIG =================
TOKEN = "8504393569:AAF2bg-rOQah3-fJPeHP4xizWYLDXlEo5Xg"
ADMIN_ID = 8477195695
WELCOME_IMAGE = "welcome.png"
QR_IMAGE = "qr_code.jpg"

DATA_FILE = "data.json"
PACK_FILE = "packages.json"

# ================= INIT =================
if not os.path.exists(DATA_FILE):
    json.dump({}, open(DATA_FILE, "w"))

if not os.path.exists(PACK_FILE):
    json.dump({"399": "2900", "699": "4500"}, open(PACK_FILE, "w"))

def load(p): return json.load(open(p))
def save(p, d): json.dump(d, open(p, "w"), indent=2)

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid == ADMIN_ID:
        kb = ReplyKeyboardMarkup(
            [["🛒 Buy UC", "💸 Price List"],
             ["👑 Owner Panel"]],
            resize_keyboard=True
        )
    else:
        kb = ReplyKeyboardMarkup(
            [["🛒 Buy UC", "💸 Price List"],
             ["📦 My Orders", "📞 Support"],
             ["❌ Cancel Order"]],
            resize_keyboard=True
        )

    text = (
        "*🔥 WELCOME TO BGMI UC SERVICE 🔥*\n\n"
        "*✅ Trusted UC Delivery*\n"
        "*⚡ Fast Manual Verification*\n"
        "*💯 Safe & Secure Payments*\n\n"
        "_👇 Option select karo_"
    )

    await update.message.reply_photo(
        photo=open(WELCOME_IMAGE, "rb"),
        caption=text,
        parse_mode="Markdown",
        reply_markup=kb
    )

# ================= TEXT HANDLER =================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load(DATA_FILE)
    packs = load(PACK_FILE)
    uid = str(update.effective_user.id)
    msg = update.message.text.strip()

    # ===== PRICE LIST =====
    if msg == "💸 Price List":
        text = "💸 *UC PRICE LIST*\n\n"
        for p, u in packs.items():
            text += f"₹{p} ➜ {u} UC\n"
        await update.message.reply_text(text, parse_mode="Markdown")
        return

    # ===== CANCEL ORDER =====
    if msg == "❌ Cancel Order":
        data.pop(uid, None)
        save(DATA_FILE, data)
        await start(update, context)
        return

    # ===== SUPPORT =====
    if msg == "📞 Support":
        await update.message.reply_text(
            "📞 *Support*\n\nOrder ID ke sath message kare\n⏰ 11AM – 10PM",
            parse_mode="Markdown"
        )
        return

    # ===== MY ORDERS =====
    if msg == "📦 My Orders":
        orders = [o for o in data.values() if isinstance(o, dict) and o.get("user_id") == uid]
        if not orders:
            await update.message.reply_text("📭 No orders found")
            return
        text = "📦 *Your Orders*\n\n"
        for o in orders[-5:]:
            text += f"🆔 {o['order_id']}\n💎 UC: {o['amount']}\n📌 {o['status']}\n\n"
        await update.message.reply_text(text, parse_mode="Markdown")
        return

    # ===== BUY UC =====
    if msg == "🛒 Buy UC":
        data[uid] = {"step": "BGMI"}
        save(DATA_FILE, data)
        await update.message.reply_text(
            "🎮 BGMI ID bhejo (9–10 digit)",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # ===== OWNER PANEL =====
    if msg == "👑 Owner Panel" and update.effective_user.id == ADMIN_ID:
        kb = ReplyKeyboardMarkup(
            [["➕ Add Package", "➖ Remove Package"],
             ["📦 View Packages"],
             ["📊 Bot Stats", "📢 Broadcast"]],
            resize_keyboard=True
        )
        await update.message.reply_text("👑 Owner Panel", reply_markup=kb)
        return

    # ===== BOT STATS =====
    if msg == "📊 Bot Stats" and update.effective_user.id == ADMIN_ID:
        users = set()
        pending = approved = rejected = 0
        for v in data.values():
            if isinstance(v, dict) and "user_id" in v:
                users.add(v["user_id"])
                if v["status"] == "Pending": pending += 1
                elif v["status"] == "Approved": approved += 1
                elif v["status"] == "Rejected": rejected += 1

        await update.message.reply_text(
            f"👥 Users: {len(users)}\n"
            f"⏳ Pending: {pending}\n"
            f"✅ Approved: {approved}\n"
            f"❌ Rejected: {rejected}"
        )
        return

    # ===== BROADCAST =====
    if msg == "📢 Broadcast" and update.effective_user.id == ADMIN_ID:
        data[uid] = {"step": "BROADCAST"}
        save(DATA_FILE, data)
        await update.message.reply_text("📢 Message bhejo broadcast ke liye")
        return

    if uid in data and data[uid].get("step") == "BROADCAST" and update.effective_user.id == ADMIN_ID:
        users = {int(v["user_id"]) for v in data.values() if isinstance(v, dict) and "user_id" in v}
        sent = failed = 0
        for u in users:
            try:
                await context.bot.send_message(u, msg)
                sent += 1
            except:
                failed += 1
        data.pop(uid)
        save(DATA_FILE, data)
        await update.message.reply_text(f"📢 Broadcast Done\nSent: {sent}\nFailed: {failed}")
        return

    # ===== BGMI ID STEP =====
    if uid in data and data[uid].get("step") == "BGMI":
        if not re.fullmatch(r"\d{9,10}", msg):
            await update.message.reply_text("❌ Invalid BGMI ID")
            return
        data[uid]["bgmi_id"] = msg
        data[uid]["step"] = "PACK"
        save(DATA_FILE, data)

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"₹{p} – {u} UC", callback_data=p)]
            for p, u in packs.items()
        ])
        await update.message.reply_text("📦 Package select karo", reply_markup=kb)

# ================= CALLBACK =================
async def pack_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = load(DATA_FILE)
    uid = str(q.from_user.id)

    data[uid]["amount"] = q.data
    data[uid]["step"] = "SCREENSHOT"
    save(DATA_FILE, data)

    await q.message.reply_photo(
        open(QR_IMAGE, "rb"),
        caption="💰 Payment ke baad screenshot bhejo",
        parse_mode="Markdown"
    )

# ================= PHOTO =================
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load(DATA_FILE)
    uid = str(update.effective_user.id)

    if uid not in data or data[uid].get("step") != "SCREENSHOT":
        return

    oid = str(uuid.uuid4())[:8].upper()
    data[uid].update({
        "order_id": oid,
        "user_id": uid,
        "status": "Pending",
        "time": str(datetime.now())
    })
    save(DATA_FILE, data)

    await update.message.forward(ADMIN_ID)
    await update.message.reply_text(f"✅ Order Submitted\n🆔 {oid}")

# ================= RUN =================
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, text_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(CallbackQueryHandler(pack_handler, pattern="^\d+$"))
    print("✅ BOT RUNNING")
    app.run_polling()

if __name__ == "__main__":
    main()