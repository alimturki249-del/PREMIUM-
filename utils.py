import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_all_plans, get_setting


PLAN_ICONS = ["💎", "⚡", "👑", "🌟", "🔥", "💫", "🎯", "🚀"]


def plans_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    plans = get_all_plans()
    if not plans:
        return None, None
    for i, plan in enumerate(plans):
        icon = PLAN_ICONS[i % len(PLAN_ICONS)]
        btn = InlineKeyboardButton(
            text=f"{icon} {plan['name']} — ₹{plan['price']:.0f}",
            callback_data=f"plan_{plan['id']}"
        )
        markup.add(btn)
    return markup, plans


def home_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("💎 Buy Subscription", callback_data="buy_subscription"),
        InlineKeyboardButton("📞 Support", callback_data="support")
    )
    return markup


def payment_confirm_keyboard(plan_id: int):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("✅ I've Paid", callback_data=f"paid_{plan_id}"),
        InlineKeyboardButton("🔙 Back to Plans", callback_data="buy_subscription")
    )
    return markup


def admin_approve_reject_keyboard(payment_id: int):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{payment_id}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{payment_id}")
    )
    return markup


def admin_panel_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("➕ Add Plan", callback_data="admin_addplan"),
        InlineKeyboardButton("📋 View Plans", callback_data="admin_plans"),
        InlineKeyboardButton("✏️ Edit Plan", callback_data="admin_editplan"),
        InlineKeyboardButton("🗑 Delete Plan", callback_data="admin_deleteplan"),
        InlineKeyboardButton("💳 Set UPI", callback_data="admin_setupi"),
        InlineKeyboardButton("👋 Set Welcome", callback_data="admin_setwelcome"),
        InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
        InlineKeyboardButton("📊 Statistics", callback_data="admin_stats"),
    )
    return markup


def cancel_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"))
    return markup


def back_to_admin_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel"))
    return markup


def format_plan_detail(plan, icon="💎"):
    channels = plan["channel_links"].split(",")
    channel_list = "\n".join([f"   🔗 {c.strip()}" for c in channels])
    return (
        f"{icon} <b>{plan['name']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Price:</b> ₹{plan['price']:.0f}\n"
        f"📅 <b>Validity:</b> {plan['validity_days']} Days\n"
        f"📡 <b>Channels:</b>\n{channel_list}\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )
