from typing import Optional

from pydantic import BaseModel


class Ens(BaseModel):
    ens_name: str
    owner: Optional[str]
    address: Optional[str]
    twitter: Optional[str]
    twitter_handle: Optional[str]
    github: Optional[str]
    email: Optional[str]
    url: Optional[str]
    discord: Optional[str]
    reddit: Optional[str]
    telegram: Optional[str]
