# Базовые настройки бота
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
ADMIN_ID = 123456789
ADMINS = [ADMIN_ID]
MODERATORS = []
HELPER_ID = ADMIN_ID

# Telegram API (для Telethon)
API_ID = 123456
API_HASH = "YOUR_TELEGRAM_API_HASH_HERE"

# YooMoney
YOOMONEY_WALLET = ""

# База данных
# Если оставить пустым или None — будет использован SQLite: sqlite:///shop.db
DB_URL = "sqlite:///shop.db"

# LZT Market
LZT_API_TOKEN = "YOUR_LZT_API_TOKEN_HERE"
LZT_PROXY = None

# Webhook / Flask
WEBHOOK_PORT = 8080

# Страны и номера телефонов
COUNTRIES = [
    {"code": "RU", "name": "Россия", "flag": "🇷🇺", "phone_code": "+7"},
    {"code": "UA", "name": "Украина", "flag": "🇺🇦", "phone_code": "+380"},
    {"code": "KZ", "name": "Казахстан", "flag": "🇰🇿", "phone_code": "+7"},
]

# Пример PostgreSQL:
# DB_URL = "postgresql://user:password@localhost:5432/numbershop"

# Пример для реального запуска:
# BOT_TOKEN = "123456:ABCDEF..."
# ADMIN_ID = 123456789
# API_ID = 123456
# API_HASH = "abcdef1234567890..."
# YOOMONEY_WALLET = "410011..."
# LZT_API_TOKEN = "..."
