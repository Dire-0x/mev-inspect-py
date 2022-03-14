from sqlalchemy import Column, String

from .base import Base


class EnsModel(Base):
    __tablename__ = "ens"

    ens_name = Column(String, primary_key=True)
    owner = Column(String, nullable=True)
    address = Column(String, nullable=True)
    twitter = Column(String, nullable=True)
    twitter_handle = Column(String, nullable=True)
    github = Column(String, nullable=True)
    email = Column(String, nullable=True)
    url = Column(String, nullable=True)
    discord = Column(String, nullable=True)
    reddit = Column(String, nullable=True)
    telegram = Column(String, nullable=True)
