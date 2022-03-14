from datetime import datetime
from typing import List

from sqlalchemy import orm

from mev_inspect.db import write_as_csv
from mev_inspect.models.blocks import BlockModel
from mev_inspect.schemas.blocks import Block


def delete_blocks(
    db_session,
    after_block_number: int,
    before_block_number: int,
) -> None:
    db_session.execute(
        """
        DELETE FROM blocks
        WHERE
            block_number >= :after_block_number AND
            block_number < :before_block_number
        """,
        params={
            "after_block_number": after_block_number,
            "before_block_number": before_block_number,
        },
    )
    db_session.commit()


def write_blocks(
    db_session,
    blocks: List[Block],
) -> None:
    items_generator = (
        (
            block.block_number,
            datetime.fromtimestamp(block.block_timestamp),
        )
        for block in blocks
    )
    write_as_csv(db_session, "blocks", items_generator)


def get_blocks(db_session: orm.Session, blocks: List[int]) -> List[BlockModel]:
    if len(blocks) < 1:
        return []
    filterString = f"IN {tuple(blocks)}"
    if len(blocks) <= 1:
        filterString = f"= '{blocks[0]}'"
    result = db_session.execute(
        f"SELECT * FROM blocks WHERE block_number {filterString}"
    ).all()
    return result
