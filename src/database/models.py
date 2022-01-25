import datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String

from .database import Base


class House(Base):
    __tablename__ = "t_house"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    url = Column(String)
    sell_detail = Column(JSON)
    base_content = Column(JSON)
    transaction_content = Column(JSON)
    des_content = Column(JSON)
    create_time = Column(DateTime(timezone=True), default=datetime.datetime.now)
