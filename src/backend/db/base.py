import sys
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker


Base = declarative_base()

# Путь к базе
DB_PATH = Path(sys.argv[0]).resolve().parent / "rao.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Создание движка
Engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)


# Принудительно включаем внешние ключи для SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


# Фабрика сессий
SessionFactory = sessionmaker(bind=Engine, autoflush=False, future=True)
