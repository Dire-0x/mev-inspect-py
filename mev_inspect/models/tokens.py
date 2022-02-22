from sqlalchemy import Column, Numeric, String

from .base import Base


class TokenModel(Base):
    __tablename__ = "tokens"

    token_address = Column(String, nullable=False, primary_key=True)
    decimals = Column(Numeric, nullable=False)
