from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from . import models, schemas


def createHouse(db: Session, house: schemas.HouseBase):
    """create house

    Args:
        db (Session): database session
        house (schemas.HouseBase): house data

    Returns:
        None
    """
    db_house = models.House(**house.dict())
    db.add(db_house)
    db.commit()
    return None


def getHouseStatement(db: Session, date_str: str):
    """get house statement

    Args:
        db (Session): database session
        date_str (str): date

    Returns:
        SQLAlchemy Selectable
    """
    return (
        db.query(
            models.House.sell_detail["resblockPosition"],
            models.House.sell_detail["resblockName"],
            models.House.sell_detail["area"],
            models.House.sell_detail["totalPrice"],
            models.House.sell_detail["price"],
            models.House.base_content["房屋户型"],
            models.House.url,
        )
        .filter(func.strftime("%Y-%m-%d", models.House.create_time) == date_str)
        .distinct()
        .statement
    )
