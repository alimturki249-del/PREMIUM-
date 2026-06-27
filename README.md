# 🤖 Premium Telegram Subscription Bot

A **production-ready** Telegram subscription bot built with Python + pyTelegramBotAPI and SQLite. Supports UPI QR code payments, multi-channel plans, admin panel, broadcast, and full payment verification workflow.

---

## 📁 Project Structure

```
subscription_bot/
├── bot.py                  # Entry point
├── config.py               # Environment config loader
├── database.py             # SQLite ORM — all DB operations
├── qr_generator.py         # UPI QR code image generator (Pillow + qrcode)
├── utils.py                # Keyboards, formatters, shared helpers
├── handlers/
│   ├── admin.py            # All admin commands & multi-step flows
│   ├── user.py             # /start, plan display, QR payment trigger
│   ├── payments.py         # UTR + screenshot submission, approve/reject
│   └── broadcast.py        # Broadcast placeholder (logic in admin.py)
├── .env.example            # Environment variable template
├── requirements.txt        # Python dependencies
└── README.md
```

---

## ⚡ Quick Start

### 1. Clone / Copy the project

```bash
cd subscription_bot
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_telegram_user_id
DB_PATH=subscription_bot.db
```

- **BOT_TOKEN** — get from [@BotFather](https://t.me/BotFather)
- **ADMIN_ID** — your Telegram numeric ID (get from [@userinfobot](https://t.me/userinfobot))

### 5. Run the bot

```bash
python bot.py
```

---

## 👑 Admin Commands

| Command | Description |
|---|---|
| `/admin` | Open the Admin Control Panel |
| `/addplan` | Create a new subscription plan (guided wizard) |
| `/editplan` | Edit an existing plan |
| `/deleteplan` | Delete a plan |
| `/plans` | View all plans |
| `/setupi` | Set your UPI ID for payments |
| `/setwelcome` | Set custom welcome message (HTML supported) |
| `/broadcast` | Broadcast any message/media to all users |
| `/stats` | View bot statistics |

---

## 👤 User Flow

```
/start
  └─▶ Welcome Message
        └─▶ [💎 Buy Subscription]
              └─▶ Plan List (inline buttons)
                    └─▶ Select Plan → UPI QR Code generated
                          └─▶ [✅ I've Paid]
                                └─▶ Enter UTR Number
                                      └─▶ Upload Screenshot
                                            └─▶ Admin Review
                                                  ├─▶ [✅ Approve] → Channel links sent to user
                                                  └─▶ [❌ Reject]  → Rejection notice sent
```

---

## 💳 Payment System

- Admin sets UPI ID via `/setupi` (stored in SQLite `settings` table)
- Bot auto-generates a styled **UPI QR code** with:
  - UPI ID
  - Exact plan amount
  - Merchant name
  - Payment note (plan name)
- QR uses the `upi://pay?...` deep-link standard (works with PhonePe, GPay, Paytm, etc.)

---

## 🔐 Security Features

| Feature | Detail |
|---|---|
| Admin-only commands | Validated by `ADMIN_ID` on every handler |
| Duplicate UTR prevention | `UNIQUE` constraint + pre-check before DB insert |
| Fake approval prevention | Status checked before approve/reject action |
| Payment state isolation | Per-user in-memory state dict, cleared on cancel/complete |
| No plaintext secrets | All config via `.env` file |

---

## 🗂 Database Schema

### `users`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | Auto increment |
| telegram_id | INTEGER UNIQUE | Telegram user ID |
| username | TEXT | @handle |
| full_name | TEXT | Display name |
| joined_at | TEXT | ISO datetime |

### `plans`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | Auto increment |
| name | TEXT | Plan name |
| price | REAL | Amount in ₹ |
| validity_days | INTEGER | Days of access |
| channel_links | TEXT | Comma-separated URLs |
| created_at | TEXT | ISO datetime |

### `payments`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | Auto increment |
| telegram_id | INTEGER | Payer's Telegram ID |
| plan_id | INTEGER FK | References plans.id |
| utr_number | TEXT UNIQUE | Transaction reference |
| screenshot_file_id | TEXT | Telegram file ID |
| status | TEXT | pending / approved / rejected |
| submitted_at | TEXT | ISO datetime |
| reviewed_at | TEXT | ISO datetime |

### `settings`
| Column | Type | Notes |
|---|---|---|
| key | TEXT PK | Setting name |
| value | TEXT | Setting value |

---

## 📦 Dependencies

```
pyTelegramBotAPI==4.18.0    # Telegram Bot API wrapper
qrcode[pil]==7.4.2          # QR code generation
Pillow==10.3.0               # Image processing for styled QR
python-dotenv==1.0.1         # .env file loader
```

SQLite3 is included with Python's standard library — no extra install needed.

---

## 🎨 UI Highlights

- **Dark-themed QR card** with rounded corners, amount in teal, subtle branding
- **Rich emoji** throughout for premium feel
- **Inline keyboards** for all interactions — no slash-command clutter for users
- **Typing actions** (`send_chat_action`) for natural response feel
- **HTML parse mode** for bold, italic, code formatting in messages

---

## 🚀 Production Tips

1. **Run with a process manager** — use `systemd`, `supervisor`, or `pm2` (via `pm2 start bot.py --interpreter python3`) to auto-restart on crash.
2. **Use webhooks instead of polling** for lower latency at scale — replace `infinity_polling` in `bot.py` with a Flask/FastAPI webhook server.
3. **Backup the SQLite database** regularly — or migrate to PostgreSQL for concurrent access.
4. **Merchant name** — set `merchant_name` in the `settings` table via a direct DB update or add an admin command for it.

---

## 📄 License

MIT — free to use, modify, and distribute.
