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
# price_rub — рекомендуемая базовая цена для такого типа номера
COUNTRIES = [
    {"code": "RU", "name": "Россия", "flag": "🇷🇺", "phone_code": "+7", "price_rub": 1800},
    {"code": "UA", "name": "Украина", "flag": "🇺🇦", "phone_code": "+380", "price_rub": 2200},
    {"code": "KZ", "name": "Казахстан", "flag": "🇰🇿", "phone_code": "+7", "price_rub": 1700},
    {"code": "BY", "name": "Беларусь", "flag": "🇧🇾", "phone_code": "+375", "price_rub": 2000},
    {"code": "UZ", "name": "Узбекистан", "flag": "🇺🇿", "phone_code": "+998", "price_rub": 1600},
    {"code": "AZ", "name": "Азербайджан", "flag": "🇦🇿", "phone_code": "+994", "price_rub": 1700},
    {"code": "GE", "name": "Грузия", "flag": "🇬🇪", "phone_code": "+995", "price_rub": 1800},
    {"code": "TR", "name": "Турция", "flag": "🇹🇷", "phone_code": "+90", "price_rub": 2100},
    {"code": "DE", "name": "Германия", "flag": "🇩🇪", "phone_code": "+49", "price_rub": 2600},
    {"code": "FR", "name": "Франция", "flag": "🇫🇷", "phone_code": "+33", "price_rub": 2500},
    {"code": "ES", "name": "Испания", "flag": "🇪🇸", "phone_code": "+34", "price_rub": 2400},
    {"code": "IT", "name": "Италия", "flag": "🇮🇹", "phone_code": "+39", "price_rub": 2500},
    {"code": "GB", "name": "Великобритания", "flag": "🇬🇧", "phone_code": "+44", "price_rub": 2800},
    {"code": "BR", "name": "Бразилия", "flag": "🇧🇷", "phone_code": "+55", "price_rub": 2300},
    {"code": "CN", "name": "Китай", "flag": "🇨🇳", "phone_code": "+86", "price_rub": 2200},
    {"code": "JP", "name": "Япония", "flag": "🇯🇵", "phone_code": "+81", "price_rub": 3000},
    {"code": "KR", "name": "Южная Корея", "flag": "🇰🇷", "phone_code": "+82", "price_rub": 2900},
    {"code": "SG", "name": "Сингапур", "flag": "🇸🇬", "phone_code": "+65", "price_rub": 2700},
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
