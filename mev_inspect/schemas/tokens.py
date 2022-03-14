from pydantic import BaseModel, validator


class Token(BaseModel):
    token_address: str
    decimals: int

    @validator("token_address")
    def lower_token_address(cls, v: str) -> str:
        return v.lower()
