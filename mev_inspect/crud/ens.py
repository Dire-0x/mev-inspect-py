import json
import logging
from typing import List

from mev_inspect.models.ens import EnsModel
from mev_inspect.schemas.ens import Ens

logger = logging.getLogger(__name__)


def write_ens(
    db_session,
    ens: List[Ens],
) -> None:
    models = [EnsModel(**json.loads(en.json())) for en in ens]
    for model in models:
        try:
            db_session.buld_save_objects([model])
            db_session.commit()
        except:
            logger.info("Error saving ens")


def get_ens_by_address(db_session, addresses: List[str]) -> List[Ens]:
    if len(addresses) == 0:
        return []
    filterString = f"IN {tuple(addresses)}"
    if len(addresses) == 1:
        filterString = f"= '{addresses[0]}'"
    ens: List[EnsModel] = db_session.execute(
        f"SELECT * from ens WHERE owner {filterString} OR address {filterString}"
    ).all()
    return [Ens(**en) for en in ens]


def get_ens_by_name(db_session, names: List[str]) -> List[Ens]:
    if len(names) == 0:
        return []
    filterString = f"IN {tuple(names)}"
    if len(names) == 1:
        filterString = f"= '{names[0]}'"
    ens: List[EnsModel] = db_session.execute(
        f"SELECT * from ens WHERE ens_name {filterString}"
    ).all()
    return [Ens(**en) for en in ens]
