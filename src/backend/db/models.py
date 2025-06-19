from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Date, Time, Text
from sqlalchemy.orm import relationship

from .base import Base


class Songs(Base):
    __tablename__ = 'songs'

    id = Column(Integer, primary_key=True)
    artist = Column(String, nullable=False)         # Исполнитель
    title = Column(String, nullable=False)          # Название
    duration = Column(Time, nullable=True)        # Время звучания (например, '5:36')
    composer = Column(String, nullable=True)        # ФИО композитора
    lyricist = Column(String, nullable=True)        # ФИО автора текста
    label = Column(String, nullable=True)           # Лейбл


class Report(Base):
    __tablename__ = 'report'

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)             # Дата
    time = Column(Time, nullable=False)             # Время
    artist = Column(String, nullable=False)         # Исполнитель
    title = Column(String, nullable=False)          # Название
    play_duration = Column(Time, nullable=True)   # Длительность звучания
    total_duration = Column(Time, nullable=True)  # Общий хронометраж
    composer = Column(String, nullable=True)        # Композитор
    lyricist = Column(String, nullable=True)        # Автор текста
    program_name = Column(String, nullable=True)    # Передача
    play_count = Column(Integer, default=1)         # Количество исполнений
    genre = Column(String, nullable=True)           # Жанр
    label = Column(String, nullable=True)           # Лейбл

    song_id = Column(Integer, ForeignKey("songs.id"), nullable=True)  # опционально
    song = relationship("Songs", backref="usages", lazy="joined")     # позволяет связывать при желании


class State(Base):
    __tablename__ = 'state'

    key = Column(String, primary_key=True)
    value = Column(JSON, nullable=False)


class Settings(Base):
    """
    ORM model for application settings.
    Each setting is stored as a key-value pair.
    """
    __tablename__ = 'settings'

    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False)
