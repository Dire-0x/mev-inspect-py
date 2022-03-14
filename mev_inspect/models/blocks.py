from sqlalchemy import Column, DateTime, Numeric

from .base import Base


class BlockModel(Base):
    __tablename__ = "blocks"

    block_number = Column(Numeric, nullable=False, primary_key=True)
    block_timestamp = Column(DateTime, nullable=False)
