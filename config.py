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
# price_rub — базовая рекомендуемая цена для номера из страны
# Список включает практически все страны мира и популярные рынки Telegram-аккаунтов.
COUNTRIES = [
    {"code": "RU", "name": "Россия", "flag": "🇷🇺", "phone_code": "+7", "price_rub": 1800},
    {"code": "UA", "name": "Украина", "flag": "🇺🇦", "phone_code": "+380", "price_rub": 2200},
    {"code": "KZ", "name": "Казахстан", "flag": "🇰🇿", "phone_code": "+7", "price_rub": 1700},
    {"code": "BY", "name": "Беларусь", "flag": "🇧🇾", "phone_code": "+375", "price_rub": 2000},
    {"code": "UZ", "name": "Узбекистан", "flag": "🇺🇿", "phone_code": "+998", "price_rub": 1600},
    {"code": "AZ", "name": "Азербайджан", "flag": "🇦🇿", "phone_code": "+994", "price_rub": 1700},
    {"code": "GE", "name": "Грузия", "flag": "🇬🇪", "phone_code": "+995", "price_rub": 1800},
    {"code": "AM", "name": "Армения", "flag": "🇦🇲", "phone_code": "+374", "price_rub": 1700},
    {"code": "MD", "name": "Молдова", "flag": "🇲🇩", "phone_code": "+373", "price_rub": 1600},
    {"code": "KG", "name": "Кыргызстан", "flag": "🇰🇬", "phone_code": "+996", "price_rub": 1600},
    {"code": "TJ", "name": "Таджикистан", "flag": "🇹🇯", "phone_code": "+992", "price_rub": 1500},
    {"code": "TM", "name": "Туркменистан", "flag": "🇹🇲", "phone_code": "+993", "price_rub": 1500},
    {"code": "TR", "name": "Турция", "flag": "🇹🇷", "phone_code": "+90", "price_rub": 2100},
    {"code": "DE", "name": "Германия", "flag": "🇩🇪", "phone_code": "+49", "price_rub": 2600},
    {"code": "FR", "name": "Франция", "flag": "🇫🇷", "phone_code": "+33", "price_rub": 2500},
    {"code": "ES", "name": "Испания", "flag": "🇪🇸", "phone_code": "+34", "price_rub": 2400},
    {"code": "IT", "name": "Италия", "flag": "🇮🇹", "phone_code": "+39", "price_rub": 2500},
    {"code": "GB", "name": "Великобритания", "flag": "🇬🇧", "phone_code": "+44", "price_rub": 2800},
    {"code": "IE", "name": "Ирландия", "flag": "🇮🇪", "phone_code": "+353", "price_rub": 2300},
    {"code": "PT", "name": "Португалия", "flag": "🇵🇹", "phone_code": "+351", "price_rub": 2200},
    {"code": "NL", "name": "Нидерланды", "flag": "🇳🇱", "phone_code": "+31", "price_rub": 2500},
    {"code": "BE", "name": "Бельгия", "flag": "🇧🇪", "phone_code": "+32", "price_rub": 2400},
    {"code": "CH", "name": "Швейцария", "flag": "🇨🇭", "phone_code": "+41", "price_rub": 2700},
    {"code": "AT", "name": "Австрия", "flag": "🇦🇹", "phone_code": "+43", "price_rub": 2500},
    {"code": "SE", "name": "Швеция", "flag": "🇸🇪", "phone_code": "+46", "price_rub": 2400},
    {"code": "NO", "name": "Норвегия", "flag": "🇳🇴", "phone_code": "+47", "price_rub": 2500},
    {"code": "FI", "name": "Финляндия", "flag": "🇫🇮", "phone_code": "+358", "price_rub": 2400},
    {"code": "DK", "name": "Дания", "flag": "🇩🇰", "phone_code": "+45", "price_rub": 2400},
    {"code": "PL", "name": "Польша", "flag": "🇵🇱", "phone_code": "+48", "price_rub": 2000},
    {"code": "CZ", "name": "Чехия", "flag": "🇨🇿", "phone_code": "+420", "price_rub": 2200},
    {"code": "SK", "name": "Словакия", "flag": "🇸🇰", "phone_code": "+421", "price_rub": 2100},
    {"code": "HU", "name": "Венгрия", "flag": "🇭🇺", "phone_code": "+36", "price_rub": 2100},
    {"code": "RO", "name": "Румыния", "flag": "🇷🇴", "phone_code": "+40", "price_rub": 2000},
    {"code": "BG", "name": "Болгария", "flag": "🇧🇬", "phone_code": "+359", "price_rub": 2000},
    {"code": "GR", "name": "Греция", "flag": "🇬🇷", "phone_code": "+30", "price_rub": 2200},
    {"code": "HR", "name": "Хорватия", "flag": "🇭🇷", "phone_code": "+385", "price_rub": 2000},
    {"code": "SI", "name": "Словения", "flag": "🇸🇮", "phone_code": "+386", "price_rub": 2000},
    {"code": "RS", "name": "Сербия", "flag": "🇷🇸", "phone_code": "+381", "price_rub": 1800},
    {"code": "AL", "name": "Албания", "flag": "🇦🇱", "phone_code": "+355", "price_rub": 1800},
    {"code": "MK", "name": "Северная Македония", "flag": "🇲🇰", "phone_code": "+389", "price_rub": 1800},
    {"code": "IS", "name": "Исландия", "flag": "🇮🇸", "phone_code": "+354", "price_rub": 2600},
    {"code": "LI", "name": "Лихтенштейн", "flag": "🇱🇮", "phone_code": "+423", "price_rub": 2600},
    {"code": "LU", "name": "Люксембург", "flag": "🇱🇺", "phone_code": "+352", "price_rub": 2500},
    {"code": "MT", "name": "Мальта", "flag": "🇲🇹", "phone_code": "+356", "price_rub": 2200},
    {"code": "AD", "name": "Андорра", "flag": "🇦🇩", "phone_code": "+376", "price_rub": 2300},
    {"code": "MC", "name": "Монако", "flag": "🇲🇨", "phone_code": "+377", "price_rub": 2600},
    {"code": "SM", "name": "Сан-Марино", "flag": "🇸🇲", "phone_code": "+378", "price_rub": 2400},
    {"code": "VA", "name": "Ватикан", "flag": "🇻🇦", "phone_code": "+379", "price_rub": 2600},
    {"code": "US", "name": "США", "flag": "🇺🇸", "phone_code": "+1", "price_rub": 3200},
    {"code": "CA", "name": "Канада", "flag": "🇨🇦", "phone_code": "+1", "price_rub": 3000},
    {"code": "AU", "name": "Австралия", "flag": "🇦🇺", "phone_code": "+61", "price_rub": 3000},
    {"code": "NZ", "name": "Новая Зеландия", "flag": "🇳🇿", "phone_code": "+64", "price_rub": 2900},
    {"code": "BR", "name": "Бразилия", "flag": "🇧🇷", "phone_code": "+55", "price_rub": 2300},
    {"code": "AR", "name": "Аргентина", "flag": "🇦🇷", "phone_code": "+54", "price_rub": 2200},
    {"code": "CL", "name": "Чили", "flag": "🇨🇱", "phone_code": "+56", "price_rub": 2200},
    {"code": "PE", "name": "Перу", "flag": "🇵🇪", "phone_code": "+51", "price_rub": 2000},
    {"code": "CO", "name": "Колумбия", "flag": "🇨🇴", "phone_code": "+57", "price_rub": 2000},
    {"code": "MX", "name": "Мексика", "flag": "🇲🇽", "phone_code": "+52", "price_rub": 2200},
    {"code": "EC", "name": "Эквадор", "flag": "🇪🇨", "phone_code": "+593", "price_rub": 1900},
    {"code": "UY", "name": "Уругвай", "flag": "🇺🇾", "phone_code": "+598", "price_rub": 2100},
    {"code": "PY", "name": "Парагвай", "flag": "🇵🇾", "phone_code": "+595", "price_rub": 1900},
    {"code": "BO", "name": "Боливия", "flag": "🇧🇴", "phone_code": "+591", "price_rub": 1800},
    {"code": "VE", "name": "Венесуэла", "flag": "🇻🇪", "phone_code": "+58", "price_rub": 2000},
    {"code": "GT", "name": "Гватемала", "flag": "🇬🇹", "phone_code": "+502", "price_rub": 1800},
    {"code": "HN", "name": "Гондурас", "flag": "🇭🇳", "phone_code": "+504", "price_rub": 1800},
    {"code": "SV", "name": "Сальвадор", "flag": "🇸🇻", "phone_code": "+503", "price_rub": 1800},
    {"code": "NI", "name": "Никарагуа", "flag": "🇳🇮", "phone_code": "+505", "price_rub": 1800},
    {"code": "CR", "name": "Коста-Рика", "flag": "🇨🇷", "phone_code": "+506", "price_rub": 1900},
    {"code": "PA", "name": "Панама", "flag": "🇵🇦", "phone_code": "+507", "price_rub": 2000},
    {"code": "DO", "name": "Доминиканская Республика", "flag": "🇩🇴", "phone_code": "+1", "price_rub": 2200},
    {"code": "PR", "name": "Пуэрто-Рико", "flag": "🇵🇷", "phone_code": "+1", "price_rub": 2200},
    {"code": "CN", "name": "Китай", "flag": "🇨🇳", "phone_code": "+86", "price_rub": 2200},
    {"code": "JP", "name": "Япония", "flag": "🇯🇵", "phone_code": "+81", "price_rub": 3000},
    {"code": "KR", "name": "Южная Корея", "flag": "🇰🇷", "phone_code": "+82", "price_rub": 2900},
    {"code": "SG", "name": "Сингапур", "flag": "🇸🇬", "phone_code": "+65", "price_rub": 2700},
    {"code": "TH", "name": "Таиланд", "flag": "🇹🇭", "phone_code": "+66", "price_rub": 2200},
    {"code": "VN", "name": "Вьетнам", "flag": "🇻🇳", "phone_code": "+84", "price_rub": 2000},
    {"code": "ID", "name": "Индонезия", "flag": "🇮🇩", "phone_code": "+62", "price_rub": 1900},
    {"code": "MY", "name": "Малайзия", "flag": "🇲🇾", "phone_code": "+60", "price_rub": 2300},
    {"code": "PH", "name": "Филиппины", "flag": "🇵🇭", "phone_code": "+63", "price_rub": 1900},
    {"code": "IN", "name": "Индия", "flag": "🇮🇳", "phone_code": "+91", "price_rub": 1600},
    {"code": "PK", "name": "Пакистан", "flag": "🇵🇰", "phone_code": "+92", "price_rub": 1500},
    {"code": "BD", "name": "Бангладеш", "flag": "🇧🇩", "phone_code": "+880", "price_rub": 1500},
    {"code": "NP", "name": "Непал", "flag": "🇳🇵", "phone_code": "+977", "price_rub": 1500},
    {"code": "LK", "name": "Шри-Ланка", "flag": "🇱🇰", "phone_code": "+94", "price_rub": 1600},
    {"code": "MN", "name": "Монголия", "flag": "🇲🇳", "phone_code": "+976", "price_rub": 1700},
    {"code": "LA", "name": "Лаос", "flag": "🇱🇦", "phone_code": "+856", "price_rub": 1700},
    {"code": "KH", "name": "Камбоджа", "flag": "🇰🇭", "phone_code": "+855", "price_rub": 1700},
    {"code": "MM", "name": "Мьянма", "flag": "🇲🇲", "phone_code": "+95", "price_rub": 1600},
    {"code": "BT", "name": "Бутан", "flag": "🇧🇹", "phone_code": "+975", "price_rub": 1700},
    {"code": "AE", "name": "ОАЭ", "flag": "🇦🇪", "phone_code": "+971", "price_rub": 2600},
    {"code": "SA", "name": "Саудовская Аравия", "flag": "🇸🇦", "phone_code": "+966", "price_rub": 2400},
    {"code": "QA", "name": "Катар", "flag": "🇶🇦", "phone_code": "+974", "price_rub": 2500},
    {"code": "KW", "name": "Кувейт", "flag": "🇰🇼", "phone_code": "+965", "price_rub": 2400},
    {"code": "BH", "name": "Бахрейн", "flag": "🇧🇭", "phone_code": "+973", "price_rub": 2300},
    {"code": "OM", "name": "Оман", "flag": "🇴🇲", "phone_code": "+968", "price_rub": 2300},
    {"code": "JO", "name": "Иордания", "flag": "🇯🇴", "phone_code": "+962", "price_rub": 2200},
    {"code": "IL", "name": "Израиль", "flag": "🇮🇱", "phone_code": "+972", "price_rub": 2600},
    {"code": "EG", "name": "Египет", "flag": "🇪🇬", "phone_code": "+20", "price_rub": 1800},
    {"code": "MA", "name": "Марокко", "flag": "🇲🇦", "phone_code": "+212", "price_rub": 1800},
    {"code": "DZ", "name": "Алжир", "flag": "🇩🇿", "phone_code": "+213", "price_rub": 1800},
    {"code": "TN", "name": "Тунис", "flag": "🇹🇳", "phone_code": "+216", "price_rub": 1800},
    {"code": "LY", "name": "Ливия", "flag": "🇱🇾", "phone_code": "+218", "price_rub": 1700},
    {"code": "MR", "name": "Мавритания", "flag": "🇲🇷", "phone_code": "+222", "price_rub": 1700},
    {"code": "GM", "name": "Гамбия", "flag": "🇬🇲", "phone_code": "+220", "price_rub": 1600},
    {"code": "SN", "name": "Сенегал", "flag": "🇸🇳", "phone_code": "+221", "price_rub": 1700},
    {"code": "ML", "name": "Мали", "flag": "🇲🇱", "phone_code": "+223", "price_rub": 1600},
    {"code": "BF", "name": "Буркина-Фасо", "flag": "🇧🇫", "phone_code": "+226", "price_rub": 1600},
    {"code": "NE", "name": "Нигер", "flag": "🇳🇪", "phone_code": "+227", "price_rub": 1600},
    {"code": "TG", "name": "Того", "flag": "🇹🇬", "phone_code": "+228", "price_rub": 1600},
    {"code": "BJ", "name": "Бенин", "flag": "🇧🇯", "phone_code": "+229", "price_rub": 1600},
    {"code": "GA", "name": "Габон", "flag": "🇬🇦", "phone_code": "+241", "price_rub": 1700},
    {"code": "CG", "name": "Республика Конго", "flag": "🇨🇬", "phone_code": "+242", "price_rub": 1700},
    {"code": "CD", "name": "ДР Конго", "flag": "🇨🇩", "phone_code": "+243", "price_rub": 1700},
    {"code": "RW", "name": "Руанда", "flag": "🇷🇼", "phone_code": "+250", "price_rub": 1700},
    {"code": "UG", "name": "Уганда", "flag": "🇺🇬", "phone_code": "+256", "price_rub": 1700},
    {"code": "TZ", "name": "Танзания", "flag": "🇹🇿", "phone_code": "+255", "price_rub": 1700},
    {"code": "ZM", "name": "Замбия", "flag": "🇿🇲", "phone_code": "+260", "price_rub": 1700},
    {"code": "MZ", "name": "Мозамбик", "flag": "🇲🇿", "phone_code": "+258", "price_rub": 1700},
    {"code": "BW", "name": "Ботсвана", "flag": "🇧🇼", "phone_code": "+267", "price_rub": 1800},
    {"code": "NA", "name": "Намибия", "flag": "🇳🇦", "phone_code": "+264", "price_rub": 1800},
    {"code": "LS", "name": "Лесото", "flag": "🇱🇸", "phone_code": "+266", "price_rub": 1800},
    {"code": "SZ", "name": "Эсватини", "flag": "🇸🇿", "phone_code": "+268", "price_rub": 1800},
    {"code": "MW", "name": "Малави", "flag": "🇲🇼", "phone_code": "+265", "price_rub": 1700},
    {"code": "AO", "name": "Ангола", "flag": "🇦🇴", "phone_code": "+244", "price_rub": 1800},
    {"code": "MG", "name": "Мадагаскар", "flag": "🇲🇬", "phone_code": "+261", "price_rub": 1800},
    {"code": "MU", "name": "Маврикий", "flag": "🇲🇺", "phone_code": "+230", "price_rub": 1900},
    {"code": "SC", "name": "Сейшельские Острова", "flag": "🇸🇨", "phone_code": "+248", "price_rub": 2000},
    {"code": "ET", "name": "Эфиопия", "flag": "🇪🇹", "phone_code": "+251", "price_rub": 1700},
    {"code": "SO", "name": "Сомали", "flag": "🇸🇴", "phone_code": "+252", "price_rub": 1700},
    {"code": "SD", "name": "Судан", "flag": "🇸🇩", "phone_code": "+249", "price_rub": 1700},
    {"code": "CM", "name": "Камерун", "flag": "🇨🇲", "phone_code": "+237", "price_rub": 1700},
    {"code": "CI", "name": "Кот-д'Ивуар", "flag": "🇨🇮", "phone_code": "+225", "price_rub": 1700},
    {"code": "GH", "name": "Гана", "flag": "🇬🇭", "phone_code": "+233", "price_rub": 1700},
    {"code": "NG", "name": "Нигерия", "flag": "🇳🇬", "phone_code": "+234", "price_rub": 1700},
    {"code": "KE", "name": "Кения", "flag": "🇰🇪", "phone_code": "+254", "price_rub": 1700},
    {"code": "ZA", "name": "ЮАР", "flag": "🇿🇦", "phone_code": "+27", "price_rub": 2100},
    {"code": "GQ", "name": "Экваториальная Гвинея", "flag": "🇬🇶", "phone_code": "+240", "price_rub": 1800},
    {"code": "CV", "name": "Кабо-Верде", "flag": "🇨🇻", "phone_code": "+238", "price_rub": 1700},
    {"code": "ST", "name": "Сан-Томе и Принсипи", "flag": "🇸🇹", "phone_code": "+239", "price_rub": 1800},
    {"code": "GN", "name": "Гвинея", "flag": "🇬🇳", "phone_code": "+224", "price_rub": 1600},
    {"code": "SL", "name": "Сьерра-Леоне", "flag": "🇸🇱", "phone_code": "+232", "price_rub": 1600},
    {"code": "LR", "name": "Либерия", "flag": "🇱🇷", "phone_code": "+231", "price_rub": 1600},
    {"code": "GM", "name": "Гамбия", "flag": "🇬🇲", "phone_code": "+220", "price_rub": 1600},
    {"code": "GN", "name": "Гвинея", "flag": "🇬🇳", "phone_code": "+224", "price_rub": 1600},
    {"code": "TD", "name": "Чад", "flag": "🇹🇩", "phone_code": "+235", "price_rub": 1600},
    {"code": "CF", "name": "ЦАР", "flag": "🇨🇫", "phone_code": "+236", "price_rub": 1600},
    {"code": "BI", "name": "Бурунди", "flag": "🇧🇮", "phone_code": "+257", "price_rub": 1700},
    {"code": "DJ", "name": "Джибути", "flag": "🇩🇯", "phone_code": "+253", "price_rub": 1700},
    {"code": "ER", "name": "Эритрея", "flag": "🇪🇷", "phone_code": "+291", "price_rub": 1700},
    {"code": "SS", "name": "Южный Судан", "flag": "🇸🇸", "phone_code": "+211", "price_rub": 1700},
    {"code": "TG", "name": "Того", "flag": "🇹🇬", "phone_code": "+228", "price_rub": 1600},
    {"code": "BJ", "name": "Бенин", "flag": "🇧🇯", "phone_code": "+229", "price_rub": 1600},
    {"code": "MZ", "name": "Мозамбик", "flag": "🇲🇿", "phone_code": "+258", "price_rub": 1700},
    {"code": "ZM", "name": "Замбия", "flag": "🇿🇲", "phone_code": "+260", "price_rub": 1700},
    {"code": "ZW", "name": "Зимбабве", "flag": "🇿🇼", "phone_code": "+263", "price_rub": 1800},
    {"code": "BW", "name": "Ботсвана", "flag": "🇧🇼", "phone_code": "+267", "price_rub": 1800},
    {"code": "NA", "name": "Намибия", "flag": "🇳🇦", "phone_code": "+264", "price_rub": 1800},
    {"code": "LS", "name": "Лесото", "flag": "🇱🇸", "phone_code": "+266", "price_rub": 1800},
    {"code": "SZ", "name": "Эсватини", "flag": "🇸🇿", "phone_code": "+268", "price_rub": 1800},
    {"code": "PG", "name": "Папуа — Новая Гвинея", "flag": "🇵🇬", "phone_code": "+675", "price_rub": 2100},
    {"code": "FJ", "name": "Фиджи", "flag": "🇫🇯", "phone_code": "+679", "price_rub": 2100},
    {"code": "SB", "name": "Соломоновы Острова", "flag": "🇸🇧", "phone_code": "+677", "price_rub": 2100},
    {"code": "VU", "name": "Вануату", "flag": "🇻🇺", "phone_code": "+678", "price_rub": 2100},
    {"code": "NC", "name": "Новая Каледония", "flag": "🇳🇨", "phone_code": "+687", "price_rub": 2200},
    {"code": "PF", "name": "Французская Полинезия", "flag": "🇵🇫", "phone_code": "+689", "price_rub": 2300},
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
