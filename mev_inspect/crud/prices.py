from typing import List

from sqlalchemy import orm
from sqlalchemy.dialects.postgresql import insert

from mev_inspect.models.prices import PriceModel
from mev_inspect.schemas.prices import Price


def write_prices(db_session: orm.Session, prices: List[Price]) -> None:
    insert_statement = (
        insert(PriceModel.__table__)
        .values([price.dict() for price in prices])
        .on_conflict_do_nothing()
    )

    db_session.execute(insert_statement)
    db_session.commit()


def get_prices(db_session: orm.Session, tokens: List[str]) -> List[Price]:
    filterString = f"IN {tuple(tokens)}"
    if len(tokens) < 1:
        return []
    if len(tokens) == 1:
        filterString = f"= '{tokens[0]}'"
    prices = db_session.execute(
        f"SELECT * FROM prices WHERE token_address {filterString} ORDER BY timestamp DESC"
    ).all()
    return prices
