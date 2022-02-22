from typing import List, Optional

from sqlalchemy.dialects.postgresql import insert

from sqlalchemy import orm

from mev_inspect.models.tokens import TokenModel
from mev_inspect.schemas.tokens import Token


def write_tokens(db_session, tokens: List[Token]) -> None:
    insert_statement = (
        insert(TokenModel.__table__)
        .values([token.dict() for token in tokens])
        .on_conflict_do_nothing()
    )

    db_session.execute(insert_statement)
    db_session.commit()

def get_tokens(db_session: orm.Session) -> Optional[List[Token]]:
    tokens = db_session.execute("SELECT * FROM tokens").all()
    return tokens
