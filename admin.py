import telebot
from telebot.types import Message, CallbackQuery
from config import ADMIN_ID
from database import (
    get_all_plans, get_plan_by_id, add_plan, delete_plan, update_plan,
    get_setting, set_setting, get_user_count, get_plan_count,
    get_payment_counts, get_today_user_count
)
from utils import (
    admin_panel_keyboard, cancel_keyboard, back_to_admin_keyboard,
    plans_keyboard, format_plan_detail, PLAN_ICONS
)

# Per-user conversation state for admin flows
admin_state = {}


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def register_admin_handlers(bot: telebot.TeleBot):

    # ──────────────────────────────────────────
    # /admin command
    # ──────────────────────────────────────────
    @bot.message_handler(commands=["admin"])
    def cmd_admin(msg: Message):
        if not is_admin(msg.from_user.id):
            bot.send_message(msg.chat.id, "⛔ <b>Access Denied.</b>", parse_mode="HTML")
            return
        bot.send_chat_action(msg.chat.id, "typing")
        bot.send_message(
            msg.chat.id,
            "👑 <b>Admin Control Panel</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Welcome back, Admin. Choose an action below.",
            parse_mode="HTML",
            reply_markup=admin_panel_keyboard()
        )

    @bot.callback_query_handler(func=lambda c: c.data == "admin_panel")
    def cb_admin_panel(call: CallbackQuery):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Access Denied.")
            return
        bot.edit_message_text(
            "👑 <b>Admin Control Panel</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Welcome back, Admin. Choose an action below.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=admin_panel_keyboard()
        )

    # ──────────────────────────────────────────
    # /stats
    # ──────────────────────────────────────────
    @bot.message_handler(commands=["stats"])
    def cmd_stats(msg: Message):
        if not is_admin(msg.from_user.id):
            return
        _send_stats(bot, msg.chat.id)

    @bot.callback_query_handler(func=lambda c: c.data == "admin_stats")
    def cb_stats(call: CallbackQuery):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Access Denied.")
            return
        bot.answer_callback_query(call.id)
        _send_stats(bot, call.message.chat.id)

    def _send_stats(bot, chat_id):
        bot.send_chat_action(chat_id, "typing")
        counts = get_payment_counts()
        text = (
            "📊 <b>Bot Statistics</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 <b>Total Users:</b> {get_user_count()}\n"
            f"🆕 <b>Today's Users:</b> {get_today_user_count()}\n"
            f"📦 <b>Total Plans:</b> {get_plan_count()}\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏳ <b>Pending Payments:</b> {counts.get('pending') or 0}\n"
            f"✅ <b>Approved Payments:</b> {counts.get('approved') or 0}\n"
            f"❌ <b>Rejected Payments:</b> {counts.get('rejected') or 0}\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=back_to_admin_keyboard())

    # ──────────────────────────────────────────
    # /plans (admin view)
    # ──────────────────────────────────────────
    @bot.message_handler(commands=["plans"])
    def cmd_plans_admin(msg: Message):
        if not is_admin(msg.from_user.id):
            return
        bot.send_chat_action(msg.chat.id, "typing")
        _send_plans_list(bot, msg.chat.id)

    @bot.callback_query_handler(func=lambda c: c.data == "admin_plans")
    def cb_admin_plans(call: CallbackQuery):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Access Denied.")
            return
        bot.answer_callback_query(call.id)
        _send_plans_list(bot, call.message.chat.id)

    def _send_plans_list(bot, chat_id):
        plans = get_all_plans()
        if not plans:
            bot.send_message(
                chat_id,
                "📦 <b>No plans found.</b>\nUse /addplan to create one.",
                parse_mode="HTML",
                reply_markup=back_to_admin_keyboard()
            )
            return
        text = "📦 <b>All Subscription Plans</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, plan in enumerate(plans):
            icon = PLAN_ICONS[i % len(PLAN_ICONS)]
            text += format_plan_detail(plan, icon) + "\n\n"
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=back_to_admin_keyboard())

    # ──────────────────────────────────────────
    # /addplan
    # ──────────────────────────────────────────
    @bot.message_handler(commands=["addplan"])
    def cmd_addplan(msg: Message):
        if not is_admin(msg.from_user.id):
            return
        _start_addplan(bot, msg.chat.id, msg.from_user.id)

    @bot.callback_query_handler(func=lambda c: c.data == "admin_addplan")
    def cb_addplan(call: CallbackQuery):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Access Denied.")
            return
        bot.answer_callback_query(call.id)
        _start_addplan(bot, call.message.chat.id, call.from_user.id)

    def _start_addplan(bot, chat_id, user_id):
        admin_state[user_id] = {"action": "addplan", "step": "name", "data": {}}
        bot.send_message(
            chat_id,
            "➕ <b>Create New Plan</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Step 1/4 — Enter the <b>Plan Name</b>:\n\n"
            "<i>Example: Premium</i>",
            parse_mode="HTML",
            reply_markup=cancel_keyboard()
        )

    # ──────────────────────────────────────────
    # /deleteplan
    # ──────────────────────────────────────────
    @bot.message_handler(commands=["deleteplan"])
    def cmd_deleteplan(msg: Message):
        if not is_admin(msg.from_user.id):
            return
        _start_deleteplan(bot, msg.chat.id, msg.from_user.id)

    @bot.callback_query_handler(func=lambda c: c.data == "admin_deleteplan")
    def cb_deleteplan(call: CallbackQuery):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Access Denied.")
            return
        bot.answer_callback_query(call.id)
        _start_deleteplan(bot, call.message.chat.id, call.from_user.id)

    def _start_deleteplan(bot, chat_id, user_id):
        plans = get_all_plans()
        if not plans:
            bot.send_message(
                chat_id,
                "📦 <b>No plans to delete.</b>",
                parse_mode="HTML",
                reply_markup=back_to_admin_keyboard()
            )
            return
        text = "🗑 <b>Delete Plan</b>\n━━━━━━━━━━━━━━━━━━━━━\nEnter the <b>Plan ID</b> to delete:\n\n"
        for i, plan in enumerate(plans):
            text += f"  <code>{plan['id']}</code> — {PLAN_ICONS[i % len(PLAN_ICONS)]} {plan['name']} (₹{plan['price']:.0f})\n"
        admin_state[user_id] = {"action": "deleteplan", "step": "id"}
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=cancel_keyboard())

    # ──────────────────────────────────────────
    # /editplan
    # ──────────────────────────────────────────
    @bot.message_handler(commands=["editplan"])
    def cmd_editplan(msg: Message):
        if not is_admin(msg.from_user.id):
            return
        _start_editplan(bot, msg.chat.id, msg.from_user.id)

    @bot.callback_query_handler(func=lambda c: c.data == "admin_editplan")
    def cb_editplan(call: CallbackQuery):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Access Denied.")
            return
        bot.answer_callback_query(call.id)
        _start_editplan(bot, call.message.chat.id, call.from_user.id)

    def _start_editplan(bot, chat_id, user_id):
        plans = get_all_plans()
        if not plans:
            bot.send_message(
                chat_id,
                "📦 <b>No plans to edit.</b>",
                parse_mode="HTML",
                reply_markup=back_to_admin_keyboard()
            )
            return
        text = "✏️ <b>Edit Plan</b>\n━━━━━━━━━━━━━━━━━━━━━\nEnter the <b>Plan ID</b> to edit:\n\n"
        for i, plan in enumerate(plans):
            text += f"  <code>{plan['id']}</code> — {PLAN_ICONS[i % len(PLAN_ICONS)]} {plan['name']} (₹{plan['price']:.0f})\n"
        admin_state[user_id] = {"action": "editplan", "step": "id", "data": {}}
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=cancel_keyboard())

    # ──────────────────────────────────────────
    # /setupi
    # ──────────────────────────────────────────
    @bot.message_handler(commands=["setupi"])
    def cmd_setupi(msg: Message):
        if not is_admin(msg.from_user.id):
            return
        _start_setupi(bot, msg.chat.id, msg.from_user.id)

    @bot.callback_query_handler(func=lambda c: c.data == "admin_setupi")
    def cb_setupi(call: CallbackQuery):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Access Denied.")
            return
        bot.answer_callback_query(call.id)
        _start_setupi(bot, call.message.chat.id, call.from_user.id)

    def _start_setupi(bot, chat_id, user_id):
        current = get_setting("upi_id") or "Not set"
        admin_state[user_id] = {"action": "setupi", "step": "upi"}
        bot.send_message(
            chat_id,
            f"💳 <b>Set UPI ID</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"Current UPI: <code>{current}</code>\n\n"
            f"Send your new <b>UPI ID</b>:\n\n"
            f"<i>Example: yourname@oksbi</i>",
            parse_mode="HTML",
            reply_markup=cancel_keyboard()
        )

    # ──────────────────────────────────────────
    # /setwelcome
    # ──────────────────────────────────────────
    @bot.message_handler(commands=["setwelcome"])
    def cmd_setwelcome(msg: Message):
        if not is_admin(msg.from_user.id):
            return
        _start_setwelcome(bot, msg.chat.id, msg.from_user.id)

    @bot.callback_query_handler(func=lambda c: c.data == "admin_setwelcome")
    def cb_setwelcome(call: CallbackQuery):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Access Denied.")
            return
        bot.answer_callback_query(call.id)
        _start_setwelcome(bot, call.message.chat.id, call.from_user.id)

    def _start_setwelcome(bot, chat_id, user_id):
        admin_state[user_id] = {"action": "setwelcome", "step": "message"}
        bot.send_message(
            chat_id,
            "👋 <b>Set Welcome Message</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Send the new welcome message.\n"
            "Supports: Text, Emoji, HTML formatting.\n\n"
            "<i>Example:</i>\n"
            "<code>🌟 Welcome to Premium Bot!\n\nGet exclusive access to our channels.</code>",
            parse_mode="HTML",
            reply_markup=cancel_keyboard()
        )

    # ──────────────────────────────────────────
    # Cancel action
    # ──────────────────────────────────────────
    @bot.callback_query_handler(func=lambda c: c.data == "cancel_action")
    def cb_cancel(call: CallbackQuery):
        uid = call.from_user.id
        if uid in admin_state:
            del admin_state[uid]
        bot.answer_callback_query(call.id, "❌ Cancelled.")
        bot.edit_message_text(
            "❌ <b>Action cancelled.</b>",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=back_to_admin_keyboard()
        )

    # ──────────────────────────────────────────
    # Universal message handler for admin flows
    # ──────────────────────────────────────────
    @bot.message_handler(
        func=lambda m: m.from_user.id == ADMIN_ID and m.from_user.id in admin_state,
        content_types=["text", "photo", "video", "animation", "document", "sticker", "voice"]
    )
    def handle_admin_flow(msg: Message):
        uid = msg.from_user.id
        state = admin_state.get(uid, {})
        action = state.get("action")

        if action == "addplan":
            _handle_addplan_flow(bot, msg, state)
        elif action == "deleteplan":
            _handle_deleteplan_flow(bot, msg, state)
        elif action == "editplan":
            _handle_editplan_flow(bot, msg, state)
        elif action == "setupi":
            _handle_setupi_flow(bot, msg, state)
        elif action == "setwelcome":
            _handle_setwelcome_flow(bot, msg, state)
        elif action == "broadcast":
            _handle_broadcast_flow(bot, msg, state)

    # ──────────────────────────────────────────
    # Add Plan flow steps
    # ──────────────────────────────────────────
    def _handle_addplan_flow(bot, msg: Message, state: dict):
        uid = msg.from_user.id
        step = state["step"]
        data = state["data"]
        text_in = msg.text.strip() if msg.text else ""

        if step == "name":
            if not text_in:
                bot.send_message(msg.chat.id, "⚠️ Plan name cannot be empty.", reply_markup=cancel_keyboard())
                return
            data["name"] = text_in
            state["step"] = "price"
            bot.send_message(
                msg.chat.id,
                "Step 2/4 — Enter the <b>Price</b> (₹):\n\n<i>Example: 199</i>",
                parse_mode="HTML", reply_markup=cancel_keyboard()
            )

        elif step == "price":
            try:
                price = float(text_in)
                if price <= 0:
                    raise ValueError
            except ValueError:
                bot.send_message(msg.chat.id, "⚠️ Enter a valid positive number.", reply_markup=cancel_keyboard())
                return
            data["price"] = price
            state["step"] = "validity"
            bot.send_message(
                msg.chat.id,
                "Step 3/4 — Enter <b>Validity</b> (Days):\n\n<i>Example: 30</i>",
                parse_mode="HTML", reply_markup=cancel_keyboard()
            )

        elif step == "validity":
            try:
                days = int(text_in)
                if days <= 0:
                    raise ValueError
            except ValueError:
                bot.send_message(msg.chat.id, "⚠️ Enter a valid positive integer.", reply_markup=cancel_keyboard())
                return
            data["validity"] = days
            state["step"] = "channels"
            bot.send_message(
                msg.chat.id,
                "Step 4/4 — Send <b>Channel Links</b> (one per line):\n\n"
                "<i>Example:\nhttps://t.me/channel1\nhttps://t.me/channel2</i>",
                parse_mode="HTML", reply_markup=cancel_keyboard()
            )

        elif step == "channels":
            lines = [l.strip() for l in text_in.splitlines() if l.strip()]
            if not lines:
                bot.send_message(msg.chat.id, "⚠️ At least one channel link required.", reply_markup=cancel_keyboard())
                return
            data["channels"] = ",".join(lines)
            plan_id = add_plan(data["name"], data["price"], data["validity"], data["channels"])
            del admin_state[uid]
            channel_preview = "\n".join([f"  🔗 {l}" for l in lines])
            bot.send_message(
                msg.chat.id,
                f"✅ <b>Plan Created Successfully!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🆔 ID: <code>{plan_id}</code>\n"
                f"📌 Name: <b>{data['name']}</b>\n"
                f"💰 Price: ₹{data['price']:.0f}\n"
                f"📅 Validity: {data['validity']} Days\n"
                f"📡 Channels:\n{channel_preview}",
                parse_mode="HTML",
                reply_markup=back_to_admin_keyboard()
            )

    # ──────────────────────────────────────────
    # Delete Plan flow
    # ──────────────────────────────────────────
    def _handle_deleteplan_flow(bot, msg: Message, state: dict):
        uid = msg.from_user.id
        text_in = msg.text.strip() if msg.text else ""
        try:
            plan_id = int(text_in)
        except ValueError:
            bot.send_message(msg.chat.id, "⚠️ Enter a valid numeric Plan ID.", reply_markup=cancel_keyboard())
            return
        plan = get_plan_by_id(plan_id)
        if not plan:
            bot.send_message(msg.chat.id, "⚠️ Plan not found.", reply_markup=cancel_keyboard())
            return
        deleted = delete_plan(plan_id)
        del admin_state[uid]
        if deleted:
            bot.send_message(
                msg.chat.id,
                f"🗑 <b>Plan Deleted</b>\n<b>{plan['name']}</b> has been removed.",
                parse_mode="HTML",
                reply_markup=back_to_admin_keyboard()
            )
        else:
            bot.send_message(msg.chat.id, "⚠️ Failed to delete plan.", reply_markup=back_to_admin_keyboard())

    # ──────────────────────────────────────────
    # Edit Plan flow
    # ──────────────────────────────────────────
    def _handle_editplan_flow(bot, msg: Message, state: dict):
        uid = msg.from_user.id
        step = state["step"]
        data = state["data"]
        text_in = msg.text.strip() if msg.text else ""

        if step == "id":
            try:
                plan_id = int(text_in)
            except ValueError:
                bot.send_message(msg.chat.id, "⚠️ Enter a valid numeric Plan ID.", reply_markup=cancel_keyboard())
                return
            plan = get_plan_by_id(plan_id)
            if not plan:
                bot.send_message(msg.chat.id, "⚠️ Plan not found.", reply_markup=cancel_keyboard())
                return
            data["plan_id"] = plan_id
            data["old"] = dict(plan)
            state["step"] = "name"
            bot.send_message(
                msg.chat.id,
                f"✏️ Editing: <b>{plan['name']}</b>\n\nEnter new <b>Plan Name</b> (or send <code>-</code> to keep current):",
                parse_mode="HTML", reply_markup=cancel_keyboard()
            )

        elif step == "name":
            old = data["old"]
            data["name"] = text_in if text_in != "-" else old["name"]
            state["step"] = "price"
            bot.send_message(
                msg.chat.id,
                f"Enter new <b>Price</b> (₹) (or send <code>-</code> to keep ₹{old['price']:.0f}):",
                parse_mode="HTML", reply_markup=cancel_keyboard()
            )

        elif step == "price":
            old = data["old"]
            if text_in == "-":
                data["price"] = old["price"]
            else:
                try:
                    data["price"] = float(text_in)
                except ValueError:
                    bot.send_message(msg.chat.id, "⚠️ Invalid price.", reply_markup=cancel_keyboard())
                    return
            state["step"] = "validity"
            bot.send_message(
                msg.chat.id,
                f"Enter new <b>Validity</b> (Days) (or send <code>-</code> to keep {old['validity_days']} days):",
                parse_mode="HTML", reply_markup=cancel_keyboard()
            )

        elif step == "validity":
            old = data["old"]
            if text_in == "-":
                data["validity"] = old["validity_days"]
            else:
                try:
                    data["validity"] = int(text_in)
                except ValueError:
                    bot.send_message(msg.chat.id, "⚠️ Invalid number.", reply_markup=cancel_keyboard())
                    return
            state["step"] = "channels"
            bot.send_message(
                msg.chat.id,
                f"Enter new <b>Channel Links</b> (one per line) (or send <code>-</code> to keep current):",
                parse_mode="HTML", reply_markup=cancel_keyboard()
            )

        elif step == "channels":
            old = data["old"]
            if text_in == "-":
                data["channels"] = old["channel_links"]
            else:
                lines = [l.strip() for l in text_in.splitlines() if l.strip()]
                data["channels"] = ",".join(lines)
            success = update_plan(data["plan_id"], data["name"], data["price"], data["validity"], data["channels"])
            del admin_state[uid]
            if success:
                bot.send_message(
                    msg.chat.id,
                    f"✅ <b>Plan Updated!</b>\n<b>{data['name']}</b> has been updated successfully.",
                    parse_mode="HTML",
                    reply_markup=back_to_admin_keyboard()
                )
            else:
                bot.send_message(msg.chat.id, "⚠️ Update failed.", reply_markup=back_to_admin_keyboard())

    # ──────────────────────────────────────────
    # Set UPI flow
    # ──────────────────────────────────────────
    def _handle_setupi_flow(bot, msg: Message, state: dict):
        uid = msg.from_user.id
        text_in = msg.text.strip() if msg.text else ""
        if not text_in or "@" not in text_in:
            bot.send_message(msg.chat.id, "⚠️ Invalid UPI ID. Must contain '@'.", reply_markup=cancel_keyboard())
            return
        set_setting("upi_id", text_in)
        del admin_state[uid]
        bot.send_message(
            msg.chat.id,
            f"✅ <b>UPI ID Updated!</b>\n\nNew UPI: <code>{text_in}</code>",
            parse_mode="HTML",
            reply_markup=back_to_admin_keyboard()
        )

    # ──────────────────────────────────────────
    # Set Welcome flow
    # ──────────────────────────────────────────
    def _handle_setwelcome_flow(bot, msg: Message, state: dict):
        uid = msg.from_user.id
        text_in = msg.text if msg.text else ""
        if not text_in.strip():
            bot.send_message(msg.chat.id, "⚠️ Welcome message cannot be empty.", reply_markup=cancel_keyboard())
            return
        set_setting("welcome_msg", text_in)
        del admin_state[uid]
        bot.send_message(
            msg.chat.id,
            f"✅ <b>Welcome Message Updated!</b>\n\nPreview:\n\n{text_in}",
            parse_mode="HTML",
            reply_markup=back_to_admin_keyboard()
        )

    # ──────────────────────────────────────────
    # Broadcast
    # ──────────────────────────────────────────
    @bot.message_handler(commands=["broadcast"])
    def cmd_broadcast(msg: Message):
        if not is_admin(msg.from_user.id):
            return
        _start_broadcast(bot, msg.chat.id, msg.from_user.id)

    @bot.callback_query_handler(func=lambda c: c.data == "admin_broadcast")
    def cb_broadcast(call: CallbackQuery):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Access Denied.")
            return
        bot.answer_callback_query(call.id)
        _start_broadcast(bot, call.message.chat.id, call.from_user.id)

    def _start_broadcast(bot, chat_id, user_id):
        admin_state[user_id] = {"action": "broadcast", "step": "message"}
        bot.send_message(
            chat_id,
            "📢 <b>Broadcast Message</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Send the message to broadcast.\n"
            "Supports: Text, Photo, Video, GIF, Sticker, Document.",
            parse_mode="HTML",
            reply_markup=cancel_keyboard()
        )

    def _handle_broadcast_flow(bot, msg: Message, state: dict):
        uid = msg.from_user.id
        del admin_state[uid]

        from database import get_all_users
        users = get_all_users()
        delivered = 0
        failed = 0

        status_msg = bot.send_message(
            msg.chat.id,
            f"📡 Broadcasting to {len(users)} users...",
            parse_mode="HTML"
        )

        for user in users:
            try:
                tid = user["telegram_id"]
                if msg.content_type == "text":
                    bot.send_message(tid, msg.text, parse_mode="HTML")
                elif msg.content_type == "photo":
                    bot.send_photo(tid, msg.photo[-1].file_id, caption=msg.caption or "", parse_mode="HTML")
                elif msg.content_type == "video":
                    bot.send_video(tid, msg.video.file_id, caption=msg.caption or "", parse_mode="HTML")
                elif msg.content_type == "animation":
                    bot.send_animation(tid, msg.animation.file_id, caption=msg.caption or "", parse_mode="HTML")
                elif msg.content_type == "document":
                    bot.send_document(tid, msg.document.file_id, caption=msg.caption or "", parse_mode="HTML")
                elif msg.content_type == "sticker":
                    bot.send_sticker(tid, msg.sticker.file_id)
                elif msg.content_type == "voice":
                    bot.send_voice(tid, msg.voice.file_id, caption=msg.caption or "", parse_mode="HTML")
                delivered += 1
            except Exception:
                failed += 1

        bot.edit_message_text(
            f"📢 <b>Broadcast Complete!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ <b>Delivered:</b> {delivered}\n"
            f"❌ <b>Failed:</b> {failed}",
            chat_id=msg.chat.id,
            message_id=status_msg.message_id,
            parse_mode="HTML",
            reply_markup=back_to_admin_keyboard()
        )

    return admin_state
