from typing import List, Optional

from pydantic import BaseModel

from .swaps import Swap


class Sandwich(BaseModel):
    id: Optional[str]
    block_number: int
    sandwicher_address: str
    frontrun_swap: Swap
    backrun_swap: Swap
    sandwiched_swaps: List[Swap]
    profit_token_address: str
    profit_amount: int
    profit_amount_decimal: Optional[float]
    profit_amount_usd: Optional[float]
