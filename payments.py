# Payment state shared across handlers
payment_state = {}

import telebot
from telebot.types import Message, CallbackQuery
from config import ADMIN_ID
from database import (
    add_payment, get_payment_by_id, update_payment_status,
    get_plan_by_id, utr_exists, get_user_count
)
from utils import admin_approve_reject_keyboard, home_keyboard


def register_payment_handlers(bot: telebot.TeleBot):

    # ──────────────────────────────────────────
    # Catch UTR and Screenshot from users in payment flow
    # ──────────────────────────────────────────
    @bot.message_handler(
        func=lambda m: m.from_user.id in payment_state,
        content_types=["text", "photo"]
    )
    def handle_payment_flow(msg: Message):
        uid = msg.from_user.id
        state = payment_state.get(uid, {})
        step = state.get("step")

        if step == "utr":
            _handle_utr_step(bot, msg, state)
        elif step == "screenshot":
            _handle_screenshot_step(bot, msg, state)

    def _handle_utr_step(bot, msg: Message, state: dict):
        uid = msg.from_user.id
        utr = msg.text.strip() if msg.text else ""

        if not utr or not utr.isdigit() or len(utr) < 10:
            bot.send_message(
                msg.chat.id,
                "⚠️ <b>Invalid UTR Number.</b>\n"
                "Please send a valid UTR/transaction reference number (numeric, at least 10 digits).",
                parse_mode="HTML"
            )
            return

        if utr_exists(utr):
            bot.send_message(
                msg.chat.id,
                "⚠️ <b>Duplicate UTR!</b>\n"
                "This UTR number has already been used.\n"
                "If you believe this is an error, contact support.",
                parse_mode="HTML",
                reply_markup=home_keyboard()
            )
            del payment_state[uid]
            return

        state["utr"] = utr
        state["step"] = "screenshot"

        bot.send_message(
            msg.chat.id,
            "📸 <b>Step 2:</b> Now send your <b>Payment Screenshot</b>\n\n"
            "<i>Upload a clear screenshot showing the successful transaction.</i>",
            parse_mode="HTML",
            reply_markup=telebot.types.InlineKeyboardMarkup().add(
                telebot.types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")
            )
        )

    def _handle_screenshot_step(bot, msg: Message, state: dict):
        uid = msg.from_user.id

        if msg.content_type != "photo" or not msg.photo:
            bot.send_message(
                msg.chat.id,
                "⚠️ Please send a <b>photo</b> (screenshot) of your payment.",
                parse_mode="HTML"
            )
            return

        plan_id = state["plan_id"]
        utr = state["utr"]
        screenshot_file_id = msg.photo[-1].file_id

        # Store payment in DB
        payment_id = add_payment(uid, plan_id, utr, screenshot_file_id)

        if payment_id is None:
            bot.send_message(
                msg.chat.id,
                "⚠️ <b>Duplicate UTR detected.</b>\nThis transaction has already been submitted.",
                parse_mode="HTML",
                reply_markup=home_keyboard()
            )
            del payment_state[uid]
            return

        del payment_state[uid]

        plan = get_plan_by_id(plan_id)
        user = msg.from_user
        username = f"@{user.username}" if user.username else "No username"

        # Notify user
        bot.send_message(
            msg.chat.id,
            "⏳ <b>Payment Submitted!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 Plan: <b>{plan['name']}</b>\n"
            f"💰 Amount: ₹{plan['price']:.0f}\n"
            f"📋 UTR: <code>{utr}</code>\n\n"
            "Your payment is under review. You will be notified once approved.\n"
            "<i>This usually takes a few minutes.</i>",
            parse_mode="HTML",
            reply_markup=home_keyboard()
        )

        # Forward to admin
        admin_caption = (
            f"🔔 <b>New Payment Request</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>User:</b> {user.full_name}\n"
            f"🔖 <b>Username:</b> {username}\n"
            f"🆔 <b>Telegram ID:</b> <code>{uid}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 <b>Plan:</b> {plan['name']}\n"
            f"💰 <b>Amount:</b> ₹{plan['price']:.0f}\n"
            f"📅 <b>Validity:</b> {plan['validity_days']} Days\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📋 <b>UTR Number:</b> <code>{utr}</code>\n"
            f"🆔 <b>Payment ID:</b> <code>{payment_id}</code>"
        )

        try:
            bot.send_photo(
                ADMIN_ID,
                photo=screenshot_file_id,
                caption=admin_caption,
                parse_mode="HTML",
                reply_markup=admin_approve_reject_keyboard(payment_id)
            )
        except Exception as e:
            print(f"[ERROR] Could not forward payment to admin: {e}")

    # ──────────────────────────────────────────
    # Admin: Approve Payment
    # ──────────────────────────────────────────
    @bot.callback_query_handler(func=lambda c: c.data.startswith("approve_"))
    def cb_approve_payment(call: CallbackQuery):
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "⛔ Access Denied.")
            return

        payment_id = int(call.data.split("_")[1])
        payment = get_payment_by_id(payment_id)

        if not payment:
            bot.answer_callback_query(call.id, "⚠️ Payment not found.")
            return

        if payment["status"] != "pending":
            bot.answer_callback_query(call.id, f"⚠️ Already {payment['status']}.")
            return

        update_payment_status(payment_id, "approved")

        plan = get_plan_by_id(payment["plan_id"])
        channels = [c.strip() for c in plan["channel_links"].split(",")]
        channel_lines = "\n".join([f"🔗 <a href='{c}'>{c}</a>" for c in channels])

        # Notify user
        try:
            bot.send_message(
                payment["telegram_id"],
                f"🎉 <b>Payment Approved!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"Your subscription has been activated successfully.\n\n"
                f"📌 <b>Plan:</b> {plan['name']}\n"
                f"📅 <b>Validity:</b> {plan['validity_days']} Days\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📡 <b>Your Premium Channels:</b>\n\n"
                f"{channel_lines}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"Thank you for subscribing! Enjoy your premium content. 🌟",
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=home_keyboard()
            )
        except Exception as e:
            print(f"[ERROR] Could not notify user {payment['telegram_id']}: {e}")

        # Update admin message
        bot.answer_callback_query(call.id, "✅ Payment Approved!")
        try:
            original_caption = call.message.caption or ""
            bot.edit_message_caption(
                caption=original_caption + "\n\n✅ <b>STATUS: APPROVED</b>",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML"
            )
        except Exception:
            pass

    # ──────────────────────────────────────────
    # Admin: Reject Payment
    # ──────────────────────────────────────────
    @bot.callback_query_handler(func=lambda c: c.data.startswith("reject_"))
    def cb_reject_payment(call: CallbackQuery):
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "⛔ Access Denied.")
            return

        payment_id = int(call.data.split("_")[1])
        payment = get_payment_by_id(payment_id)

        if not payment:
            bot.answer_callback_query(call.id, "⚠️ Payment not found.")
            return

        if payment["status"] != "pending":
            bot.answer_callback_query(call.id, f"⚠️ Already {payment['status']}.")
            return

        update_payment_status(payment_id, "rejected")

        # Notify user
        try:
            bot.send_message(
                payment["telegram_id"],
                "❌ <b>Payment Rejected</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "Your payment could not be verified.\n\n"
                "Possible reasons:\n"
                "• Incorrect amount paid\n"
                "• Invalid or unclear screenshot\n"
                "• Duplicate transaction\n\n"
                "Please contact the admin for assistance.",
                parse_mode="HTML",
                reply_markup=home_keyboard()
            )
        except Exception as e:
            print(f"[ERROR] Could not notify user {payment['telegram_id']}: {e}")

        bot.answer_callback_query(call.id, "❌ Payment Rejected.")
        try:
            original_caption = call.message.caption or ""
            bot.edit_message_caption(
                caption=original_caption + "\n\n❌ <b>STATUS: REJECTED</b>",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML"
            )
        except Exception:
            pass
