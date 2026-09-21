from contextlib import contextmanager
from datetime import datetime

import psycopg2

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

# --------------------------------------------------------------------------- #
#                          ЗАГРУЗКА DB_URL                                    #
# --------------------------------------------------------------------------- #

try:
    from config import DB_URL
except Exception:
    DB_URL = "sqlite:///shop.db"


def _to_sync_url(url: str) -> str:
    """Приводим URL к синхронному драйверу (psycopg2 / sqlite)."""
    if not url:
        return "sqlite:///shop.db"
    # asyncpg → psycopg2
    if "+asyncpg" in url:
        url = url.replace("+asyncpg", "+psycopg2")
    # postgresql:// → postgresql+psycopg2://
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


DB_URL_SYNC = _to_sync_url(DB_URL)
_safe_url = DB_URL_SYNC.split("@")[-1] if "@" in DB_URL_SYNC else DB_URL_SYNC
print(f"🗄️  База данных: {_safe_url}")


# --------------------------------------------------------------------------- #
#                              МОДЕЛИ ТАБЛИЦ                                  #
# --------------------------------------------------------------------------- #

Base = declarative_base()


class PhoneProduct(Base):
    """Номер телефона (товар) в магазине."""
    __tablename__ = "phone_products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(32), unique=True, index=True)
    price_rub = Column(Integer, default=0)
    session = Column(Text, default="")
    lzt_item_id = Column(Integer, nullable=True)
    two_fa = Column(Text, default="")
    available = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self) -> str:
        return f"<PhoneProduct(id={self.id}, phone={self.phone}, available={self.available})>"


class Purchase(Base):
    """История покупок пользователей."""
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, index=True)
    phone = Column(String(32))
    price_rub = Column(Integer, default=0)
    session = Column(Text, default="")
    lzt_item_id = Column(Integer, nullable=True)
    two_fa = Column(Text, default="")
    country_code = Column(String(16), default="UNKNOWN")
    purchased_at = Column(DateTime, default=datetime.now)

    def __repr__(self) -> str:
        return f"<Purchase(id={self.id}, user_id={self.user_id}, phone={self.phone})>"


class Admin(Base):
    """Администраторы и модераторы."""
    __tablename__ = "admins"

    user_id = Column(BigInteger, primary_key=True)
    role = Column(String(16), default="moderator")
    added_at = Column(DateTime, default=datetime.now)

    def __repr__(self) -> str:
        return f"<Admin(user_id={self.user_id}, role={self.role})>"


class Setting(Base):
    """Ключ-значение настройки (например, LZT API токен)."""
    __tablename__ = "settings"

    key = Column(String(64), primary_key=True)
    value = Column(Text)

    def __repr__(self) -> str:
        return f"<Setting(key={self.key})>"


# --------------------------------------------------------------------------- #
#                              ПОДКЛЮЧЕНИЕ                                    #
# --------------------------------------------------------------------------- #

# Для PostgreSQL pool_pre_ping спасает от "server closed the connection"
engine = create_engine(
    DB_URL_SYNC,
    pool_pre_ping=True,
    pool_recycle=280,
    future=True,
)

Session = scoped_session(
    sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
)


@contextmanager
def session_scope():
    """Контекстный менеджер сессии: commit при успехе, rollback при ошибке."""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        Session.remove()


# --------------------------------------------------------------------------- #
#                                 УТИЛИТЫ                                     #
# --------------------------------------------------------------------------- #

def normalize_phone(phone: str) -> str:
    """Приводит номер к виду +XXXXXXXXXXX."""
    if not phone:
        return phone
    phone = phone.strip()
    if not phone.startswith("+"):
        phone = "+" + phone
    return phone


# --------------------------------------------------------------------------- #
#                     ИНИЦИАЛИЗАЦИЯ / АДМИНИСТРАТОРЫ                          #
# --------------------------------------------------------------------------- #

def init_db() -> None:
    """Создаёт все таблицы, если они ещё не существуют."""
    Base.metadata.create_all(engine)
    print("✅ Таблицы созданы/проверены")


def load_admins_from_db(default_admin_id: int):
    """
    Возвращает (admins, moderators).
    admins — главные администраторы (включая default_admin_id),
    moderators — модераторы.
    """
    with session_scope() as session:
        rows = session.query(Admin).all()
        data = [(row.user_id, row.role) for row in rows]

    admins = [default_admin_id]
    moderators = []
    for user_id, role in data:
        if role == "admin" and user_id not in admins:
            admins.append(user_id)
        elif role == "moderator" and user_id not in moderators:
            moderators.append(user_id)
    return admins, moderators


def save_admin(user_id: int, role: str = "moderator") -> bool:
    """Добавляет или обновляет администратора/модератора."""
    with session_scope() as session:
        admin = session.get(Admin, user_id)
        if admin:
            admin.role = role
        else:
            session.add(Admin(user_id=user_id, role=role, added_at=datetime.now()))
    return True


def delete_admin(user_id: int) -> bool:
    """Удаляет администратора/модератора по user_id."""
    with session_scope() as session:
        admin = session.get(Admin, user_id)
        if admin:
            session.delete(admin)
    return True


# --------------------------------------------------------------------------- #
#                                  ТОВАРЫ                                     #
# --------------------------------------------------------------------------- #

def get_phone_products():
    """Список доступных номеров (свежие — первыми)."""
    with session_scope() as session:
        return (
            session.query(PhoneProduct)
            .filter(PhoneProduct.available == 1)
            .order_by(PhoneProduct.id.desc())
            .all()
        )


def get_phone_product(product_id: int):
    """Один товар по id (или None)."""
    with session_scope() as session:
        return session.get(PhoneProduct, product_id)


def add_phone_product(
    phone: str,
    price_rub: int,
    session_str: str = "",
    lzt_item_id: int = None,
    two_fa: str = "",
) -> bool:
    """Добавляет товар или обновляет существующий по номеру телефона."""
    phone = normalize_phone(phone)
    with session_scope() as session:
        product = (
            session.query(PhoneProduct)
            .filter(PhoneProduct.phone == phone)
            .first()
        )
        if product:
            product.price_rub = price_rub
            product.session = session_str
            product.lzt_item_id = lzt_item_id
            product.two_fa = two_fa
            product.available = 1
        else:
            session.add(
                PhoneProduct(
                    phone=phone,
                    price_rub=price_rub,
                    session=session_str,
                    lzt_item_id=lzt_item_id,
                    two_fa=two_fa,
                    available=1,
                    created_at=datetime.now(),
                )
            )
    return True


def delete_phone_product(product_id: int) -> bool:
    """Удаляет товар по id."""
    with session_scope() as session:
        product = session.get(PhoneProduct, product_id)
        if product:
            session.delete(product)
    return True


def update_price_rub(product_id: int, price_rub: int) -> bool:
    with session_scope() as session:
        product = session.get(PhoneProduct, product_id)
        if product:
            product.price_rub = price_rub
    return True


# --------------------------------------------------------------------------- #
#                                 СЕССИИ                                      #
# --------------------------------------------------------------------------- #

def save_phone_session(phone: str, session_str: str) -> bool:
    """Сохраняет telethon-сессию. Товар помечается как недоступный."""
    phone = normalize_phone(phone)
    with session_scope() as session:
        product = (
            session.query(PhoneProduct)
            .filter(PhoneProduct.phone == phone)
            .first()
        )
        if product:
            product.session = session_str
            product.available = 0
        else:
            session.add(
                PhoneProduct(
                    phone=phone,
                    price_rub=0,
                    session=session_str,
                    available=0,
                    created_at=datetime.now(),
                )
            )
    return True


def get_phone_session(phone: str):
    phone = normalize_phone(phone)
    with session_scope() as session:
        product = (
            session.query(PhoneProduct)
            .filter(PhoneProduct.phone == phone)
            .first()
        )
        return product.session if product else None


# --------------------------------------------------------------------------- #
#                                 ПОКУПКИ                                     #
# --------------------------------------------------------------------------- #

def add_purchase(
    user_id: int,
    phone: str,
    price_rub: int,
    session_str: str,
    lzt_item_id: int,
    two_fa: str,
    country_code: str,
) -> bool:
    phone = normalize_phone(phone)
    with session_scope() as session:
        session.add(
            Purchase(
                user_id=user_id,
                phone=phone,
                price_rub=price_rub,
                session=session_str,
                lzt_item_id=lzt_item_id,
                two_fa=two_fa,
                country_code=country_code,
                purchased_at=datetime.now(),
            )
        )
    return True


def get_user_purchases(user_id: int):
    with session_scope() as session:
        return (
            session.query(Purchase)
            .filter(Purchase.user_id == user_id)
            .order_by(Purchase.purchased_at.desc(), Purchase.id.desc())
            .all()
        )


def get_purchase(purchase_id: int):
    with session_scope() as session:
        return session.get(Purchase, purchase_id)


def count_user_purchases(user_id: int) -> int:
    with session_scope() as session:
        return (
            session.query(Purchase)
            .filter(Purchase.user_id == user_id)
            .count()
        )


def delete_user_purchases(user_id: int) -> bool:
    with session_scope() as session:
        session.query(Purchase).filter(Purchase.user_id == user_id).delete()
    return True


# --------------------------------------------------------------------------- #
#                          НАСТРОЙКИ (LZT API)                                #
# --------------------------------------------------------------------------- #

def get_lzt_token() -> str:
    """Токен LZT: сначала из БД, затем из config.py."""
    try:
        with session_scope() as session:
            setting = session.get(Setting, "lzt_api_token")
            if setting and setting.value:
                return setting.value
    except Exception:
        pass
    try:
        from config import LZT_API_TOKEN
        return LZT_API_TOKEN
    except Exception:
        return ""


def set_lzt_token(token: str) -> bool:
    with session_scope() as session:
        setting = session.get(Setting, "lzt_api_token")
        if setting:
            setting.value = token
        else:
            session.add(Setting(key="lzt_api_token", value=token))
    return True


def init_lzt_token() -> None:
    """Переносит LZT_API_TOKEN из config.py в БД при первом запуске."""
    try:
        with session_scope() as session:
            setting = session.get(Setting, "lzt_api_token")
            if setting:
                return
            try:
                from config import LZT_API_TOKEN
            except Exception:
                return
            if LZT_API_TOKEN:
                session.add(Setting(key="lzt_api_token", value=LZT_API_TOKEN))
    except Exception:
        pass