from typing import List, Dict
from uuid import uuid4
from sqlalchemy import orm, update
from sqlalchemy.sql.expression import bindparam
from mev_inspect.models.sandwiches import SandwichModel
from mev_inspect.schemas.sandwiches import Sandwich

from .shared import delete_by_block_range


def delete_sandwiches_for_blocks(
    db_session: orm.Session,
    after_block_number: int,
    before_block_number: int,
) -> None:
    delete_by_block_range(
        db_session,
        SandwichModel,
        after_block_number,
        before_block_number,
    )
    db_session.commit()


def write_sandwiches(
    db_session: orm.Session,
    sandwiches: List[Sandwich],
) -> None:
    sandwich_models = []
    sandwiched_swaps = []

    for sandwich in sandwiches:
        sandwich_id = str(uuid4())
        sandwich_models.append(
            SandwichModel(
                id=sandwich_id,
                block_number=sandwich.block_number,
                sandwicher_address=sandwich.sandwicher_address,
                frontrun_swap_transaction_hash=sandwich.frontrun_swap.transaction_hash,
                frontrun_swap_trace_address=sandwich.frontrun_swap.trace_address,
                backrun_swap_transaction_hash=sandwich.backrun_swap.transaction_hash,
                backrun_swap_trace_address=sandwich.backrun_swap.trace_address,
                profit_token_address=sandwich.profit_token_address,
                profit_amount=sandwich.profit_amount,
                profit_amount_decimal=sandwich.profit_amount_decimal,
                profit_amount_usd=sandwich.profit_amount_usd
            )
        )

        for swap in sandwich.sandwiched_swaps:
            sandwiched_swaps.append(
                {
                    "sandwich_id": sandwich_id,
                    "block_number": swap.block_number,
                    "transaction_hash": swap.transaction_hash,
                    "trace_address": swap.trace_address,
                }
            )

    if len(sandwich_models) > 0:
        db_session.bulk_save_objects(sandwich_models)
        db_session.execute(
            """
            INSERT INTO sandwiched_swaps
            (sandwich_id, block_number, transaction_hash, trace_address)
            VALUES
            (:sandwich_id, :block_number, :transaction_hash, :trace_address)
            """,
            params=sandwiched_swaps,
        )

        db_session.commit()

def update_sandwiches(
    db_session: orm.Session,
    sandwiches: List[SandwichModel],
) -> None:
    if len(sandwiches) > 0:
        data = []
        for sandwich in sandwiches:
            data.append(sandwich.__dict__)
        db_session.bulk_update_mappings(SandwichModel, data)
        db_session.commit()

def fetch_sandwiches(
    db_session: orm.Session, 
    query: str, 
    offset: int, 
    limit: int
) -> List[Sandwich]:
    sandwiches = db_session.execute(f"SELECT * FROM sandwiches WHERE {query} LIMIT {limit} OFFSET {offset}").all()
    return sandwiches

def count_sandwiches(
    db_session: orm.Session, 
    query: str, 
) -> int:
    sandwiches = db_session.execute(f"SELECT COUNT(*) AS count_1 FROM sandwiches WHERE {query}").scalar()
    return sandwiches
