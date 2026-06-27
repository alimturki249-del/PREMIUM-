import telebot
from telebot.types import Message, CallbackQuery
from config import ADMIN_ID
from database import (
    add_user, get_setting, get_all_plans, get_plan_by_id
)
from utils import (
    home_keyboard, plans_keyboard, payment_confirm_keyboard, PLAN_ICONS
)
from qr_generator import generate_upi_qr


def register_user_handlers(bot: telebot.TeleBot):

    # ──────────────────────────────────────────
    # /start
    # ──────────────────────────────────────────
    @bot.message_handler(commands=["start"])
    def cmd_start(msg: Message):
        user = msg.from_user
        add_user(user.id, user.username, user.full_name)
        bot.send_chat_action(msg.chat.id, "typing")

        welcome = get_setting("welcome_msg")
        if not welcome:
            welcome = (
                "🌟 <b>Welcome to Premium Subscription Bot!</b>\n\n"
                "Get exclusive access to our premium channels.\n"
                "Choose a plan and enjoy unlimited content. 🎯"
            )

        bot.send_message(
            msg.chat.id,
            welcome,
            parse_mode="HTML",
            reply_markup=home_keyboard()
        )

    # ──────────────────────────────────────────
    # Buy Subscription button
    # ──────────────────────────────────────────
    @bot.callback_query_handler(func=lambda c: c.data == "buy_subscription")
    def cb_buy_subscription(call: CallbackQuery):
        bot.answer_callback_query(call.id)
        bot.send_chat_action(call.message.chat.id, "typing")

        markup, plans = plans_keyboard()
        if not plans:
            bot.send_message(
                call.message.chat.id,
                "😔 <b>No plans available right now.</b>\nPlease check back later.",
                parse_mode="HTML",
                reply_markup=home_keyboard()
            )
            return

        bot.send_message(
            call.message.chat.id,
            "💎 <b>Choose Your Subscription Plan</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Select a plan to view details and payment options:",
            parse_mode="HTML",
            reply_markup=markup
        )

    # ──────────────────────────────────────────
    # Support button
    # ──────────────────────────────────────────
    @bot.callback_query_handler(func=lambda c: c.data == "support")
    def cb_support(call: CallbackQuery):
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            "📞 <b>Support</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "For any assistance, please contact our admin.\n\n"
            "⏰ Response time: Usually within a few hours.",
            parse_mode="HTML",
            reply_markup=home_keyboard()
        )

    # ──────────────────────────────────────────
    # Plan selected → Show QR
    # ──────────────────────────────────────────
    @bot.callback_query_handler(func=lambda c: c.data.startswith("plan_"))
    def cb_plan_selected(call: CallbackQuery):
        bot.answer_callback_query(call.id)
        bot.send_chat_action(call.message.chat.id, "upload_photo")

        plan_id = int(call.data.split("_")[1])
        plan = get_plan_by_id(plan_id)
        if not plan:
            bot.send_message(call.message.chat.id, "⚠️ Plan not found.", parse_mode="HTML")
            return

        upi_id = get_setting("upi_id")
        if not upi_id:
            bot.send_message(
                call.message.chat.id,
                "⚠️ <b>Payment not configured yet.</b>\nPlease contact support.",
                parse_mode="HTML"
            )
            return

        merchant_name = get_setting("merchant_name") or "Premium Bot"
        note = f"{plan['name']} Subscription"

        qr_buf = generate_upi_qr(
            upi_id=upi_id,
            amount=float(plan["price"]),
            name=merchant_name,
            note=note
        )

        channels = plan["channel_links"].split(",")
        channel_count = len(channels)

        caption = (
            f"💳 <b>Payment Details</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 <b>Plan:</b> {plan['name']}\n"
            f"💰 <b>Amount:</b> ₹{plan['price']:.0f}\n"
            f"📅 <b>Validity:</b> {plan['validity_days']} Days\n"
            f"📡 <b>Channels:</b> {channel_count} included\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏦 <b>UPI ID:</b> <code>{upi_id}</code>\n\n"
            f"📱 Scan the QR code above or use the UPI ID to pay exactly <b>₹{plan['price']:.0f}</b>.\n\n"
            f"⚠️ <i>Do not modify the amount. Incorrect payments will be rejected.</i>"
        )

        bot.send_photo(
            call.message.chat.id,
            photo=qr_buf,
            caption=caption,
            parse_mode="HTML",
            reply_markup=payment_confirm_keyboard(plan_id)
        )

    # ──────────────────────────────────────────
    # "I've Paid" button → Start payment verification
    # ──────────────────────────────────────────
    @bot.callback_query_handler(func=lambda c: c.data.startswith("paid_"))
    def cb_paid(call: CallbackQuery):
        bot.answer_callback_query(call.id)
        plan_id = int(call.data.split("_")[1])
        plan = get_plan_by_id(plan_id)
        if not plan:
            bot.send_message(call.message.chat.id, "⚠️ Plan not found.")
            return

        # Store pending payment info in user state (handled in payments.py)
        # Signal payments handler via a specially-tagged message
        bot.send_message(
            call.message.chat.id,
            f"✅ <b>Payment Confirmation</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"Plan: <b>{plan['name']}</b> | ₹{plan['price']:.0f}\n\n"
            f"📋 <b>Step 1:</b> Send your <b>UTR Number</b>\n"
            f"<i>(12-digit transaction reference number)</i>",
            parse_mode="HTML",
            reply_markup=telebot.types.InlineKeyboardMarkup().add(
                telebot.types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")
            )
        )

        # Store pending state for the payment flow (payments handler picks it up)
        from handlers.payments import payment_state
        payment_state[call.from_user.id] = {
            "step": "utr",
            "plan_id": plan_id
        }

    @bot.callback_query_handler(func=lambda c: c.data == "cancel_payment")
    def cb_cancel_payment(call: CallbackQuery):
        from handlers.payments import payment_state
        if call.from_user.id in payment_state:
            del payment_state[call.from_user.id]
        bot.answer_callback_query(call.id, "❌ Payment cancelled.")
        bot.edit_message_text(
            "❌ <b>Payment cancelled.</b>\nYou can restart anytime.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=home_keyboard()
        )
