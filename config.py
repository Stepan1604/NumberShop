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
DB_URL = "sqlite:///shop.db"

# LZT Market
LZT_API_TOKEN = "YOUR_LZT_API_TOKEN_HERE"
LZT_PROXY = None

# Webhook / Flask
WEBHOOK_PORT = 8080

# Страны и номера телефонов
# price_rub — базовая рекомендуемая цена в рублях.
# Цены снижены до более доступного диапазона: примерно 50–320 ₽.
COUNTRIES = [
    {"code": "RU", "name": "Россия", "flag": "🇷🇺", "phone_code": "+7", "price_rub": 180},
    {"code": "UA", "name": "Украина", "flag": "🇺🇦", "phone_code": "+380", "price_rub": 220},
    {"code": "KZ", "name": "Казахстан", "flag": "🇰🇿", "phone_code": "+7", "price_rub": 170},
    {"code": "BY", "name": "Беларусь", "flag": "🇧🇾", "phone_code": "+375", "price_rub": 200},
    {"code": "UZ", "name": "Узбекистан", "flag": "🇺🇿", "phone_code": "+998", "price_rub": 160},
    {"code": "AZ", "name": "Азербайджан", "flag": "🇦🇿", "phone_code": "+994", "price_rub": 170},
    {"code": "GE", "name": "Грузия", "flag": "🇬🇪", "phone_code": "+995", "price_rub": 180},
    {"code": "AM", "name": "Армения", "flag": "🇦🇲", "phone_code": "+374", "price_rub": 170},
    {"code": "MD", "name": "Молдова", "flag": "🇲🇩", "phone_code": "+373", "price_rub": 160},
    {"code": "KG", "name": "Кыргызстан", "flag": "🇰🇬", "phone_code": "+996", "price_rub": 160},
    {"code": "TJ", "name": "Таджикистан", "flag": "🇹🇯", "phone_code": "+992", "price_rub": 150},
    {"code": "TR", "name": "Турция", "flag": "🇹🇷", "phone_code": "+90", "price_rub": 210},
    {"code": "DE", "name": "Германия", "flag": "🇩🇪", "phone_code": "+49", "price_rub": 260},
    {"code": "FR", "name": "Франция", "flag": "🇫🇷", "phone_code": "+33", "price_rub": 250},
    {"code": "ES", "name": "Испания", "flag": "🇪🇸", "phone_code": "+34", "price_rub": 240},
    {"code": "IT", "name": "Италия", "flag": "🇮🇹", "phone_code": "+39", "price_rub": 250},
    {"code": "GB", "name": "Великобритания", "flag": "🇬🇧", "phone_code": "+44", "price_rub": 280},
    {"code": "PL", "name": "Польша", "flag": "🇵🇱", "phone_code": "+48", "price_rub": 200},
    {"code": "CZ", "name": "Чехия", "flag": "🇨🇿", "phone_code": "+420", "price_rub": 220},
    {"code": "RO", "name": "Румыния", "flag": "🇷🇴", "phone_code": "+40", "price_rub": 200},
    {"code": "US", "name": "США", "flag": "🇺🇸", "phone_code": "+1", "price_rub": 320},
    {"code": "CA", "name": "Канада", "flag": "🇨🇦", "phone_code": "+1", "price_rub": 300},
    {"code": "AU", "name": "Австралия", "flag": "🇦🇺", "phone_code": "+61", "price_rub": 300},
    {"code": "BR", "name": "Бразилия", "flag": "🇧🇷", "phone_code": "+55", "price_rub": 230},
    {"code": "AR", "name": "Аргентина", "flag": "🇦🇷", "phone_code": "+54", "price_rub": 220},
    {"code": "MX", "name": "Мексика", "flag": "🇲🇽", "phone_code": "+52", "price_rub": 220},
    {"code": "CN", "name": "Китай", "flag": "🇨🇳", "phone_code": "+86", "price_rub": 220},
    {"code": "JP", "name": "Япония", "flag": "🇯🇵", "phone_code": "+81", "price_rub": 300},
    {"code": "KR", "name": "Южная Корея", "flag": "🇰🇷", "phone_code": "+82", "price_rub": 290},
    {"code": "SG", "name": "Сингапур", "flag": "🇸🇬", "phone_code": "+65", "price_rub": 270},
    {"code": "TH", "name": "Таиланд", "flag": "🇹🇭", "phone_code": "+66", "price_rub": 220},
    {"code": "VN", "name": "Вьетнам", "flag": "🇻🇳", "phone_code": "+84", "price_rub": 200},
    {"code": "ID", "name": "Индонезия", "flag": "🇮🇩", "phone_code": "+62", "price_rub": 190},
    {"code": "MY", "name": "Малайзия", "flag": "🇲🇾", "phone_code": "+60", "price_rub": 230},
    {"code": "PH", "name": "Филиппины", "flag": "🇵🇭", "phone_code": "+63", "price_rub": 190},
    {"code": "IN", "name": "Индия", "flag": "🇮🇳", "phone_code": "+91", "price_rub": 160},
    {"code": "PK", "name": "Пакистан", "flag": "🇵🇰", "phone_code": "+92", "price_rub": 150},
    {"code": "BD", "name": "Бангладеш", "flag": "🇧🇩", "phone_code": "+880", "price_rub": 150},
    {"code": "AE", "name": "ОАЭ", "flag": "🇦🇪", "phone_code": "+971", "price_rub": 260},
    {"code": "SA", "name": "Саудовская Аравия", "flag": "🇸🇦", "phone_code": "+966", "price_rub": 240},
    {"code": "EG", "name": "Египет", "flag": "🇪🇬", "phone_code": "+20", "price_rub": 180},
    {"code": "MA", "name": "Марокко", "flag": "🇲🇦", "phone_code": "+212", "price_rub": 180},
    {"code": "ZA", "name": "ЮАР", "flag": "🇿🇦", "phone_code": "+27", "price_rub": 210},
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
