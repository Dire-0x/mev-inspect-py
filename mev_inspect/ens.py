import json
import logging
import os
from pathlib import Path
from typing import List

import requests
from web3 import HTTPProvider, Web3

from ens import ENS
from mev_inspect.crud.ens import get_ens_by_name
from mev_inspect.schemas.ens import Ens
from mev_inspect.schemas.sandwiches import Sandwich

logger = logging.getLogger(__name__)

THIS_FILE_DIRECTORY = Path(__file__).parents[0]
REVERSE_RECORD_ABI_FILE_PATH = (
    THIS_FILE_DIRECTORY / "abis" / "ens" / "ReverseRecord.json"
)
PUBLIC_RESOLVER_ABI_FILE_PATH = (
    THIS_FILE_DIRECTORY / "abis" / "ens" / "PublicResolver.json"
)
rr = open(REVERSE_RECORD_ABI_FILE_PATH)
pr = open(PUBLIC_RESOLVER_ABI_FILE_PATH)
REVERSE_RECORD_ABI = json.load(rr)
PUBLIC_RESOLVER_ABI = json.load(pr)
REVERSE_RECORD_CONTRACT_ADDRESS = "0x3671aE578E63FdF66ad4F3E12CC0c0d71Ac7510C"
PUBLIC_RESOLVER_CONTRACT_ADDRESS = "0x4976fb03C32e5B8cfe2b6cCB31c09Ba78EBaBa41"
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

ENS_GRAPH_URL = "https://api.thegraph.com/subgraphs/name/ensdomains/ens"


def get_ens_from_sandwiches(sandwiches: List[Sandwich], db_session) -> List[Ens]:
    addresses: List[str] = []
    for sandwich in sandwiches:
        for swap in sandwich.sandwiched_swaps:
            if swap.transaction_eoa and swap.transaction_eoa not in addresses:
                addresses.append(swap.transaction_eoa)

    ens_list = fetch_ens_names([Web3.toChecksumAddress(en) for en in addresses])
    db_result = get_ens_by_name(db_session, [ens.ens_name for ens in ens_list])

    names_in_db = [ens.ens_name for ens in db_result]
    result = []
    for ens in ens_list:
        if ens.ens_name not in names_in_db:
            result.append(ens)
    return result


def fetch_ens_names(addresses: List[str]) -> List[Ens]:
    if len(addresses) == 0:
        return []

    base_provider = HTTPProvider(os.environ["RPC_URL"])
    w3 = Web3(base_provider)
    ns = ENS.fromWeb3(w3)
    ens_list = []

    resolver = w3.eth.contract(
        w3.toChecksumAddress(PUBLIC_RESOLVER_CONTRACT_ADDRESS), abi=PUBLIC_RESOLVER_ABI
    )

    domains = fetch_from_graph(addresses)

    def value_or_none(value):
        if value == "":
            return None
        return value

    for domain in domains:
        name = domain["name"]
        if "[" in name or "]" in name:
            continue
        owner = domain["owner"]["id"]
        res = domain["resolver"]
        texts = res["texts"] if res else None
        resolver_address = (
            res["addr"]["id"]
            if res and res["addr"] and res["addr"]["id"] != ZERO_ADDRESS
            else None
        )
        nameHash = ns.namehash(name)
        ens = Ens(ens_name=name, owner=owner, address=resolver_address)
        resolver_ = ns.resolver(name)
        if texts and resolver_ and resolver_.address == resolver.address:
            if "com.twitter" in texts:
                ens.twitter = value_or_none(
                    resolver.functions.text(nameHash, "com.twitter").call()
                )
            if "com.github" in texts:
                ens.github = value_or_none(
                    resolver.functions.text(nameHash, "com.github").call()
                )
            if "email" in texts:
                ens.email = value_or_none(
                    resolver.functions.text(nameHash, "email").call()
                )
            if "url" in texts:
                ens.url = value_or_none(resolver.functions.text(nameHash, "url").call())
            if "com.discord" in texts:
                ens.discord = value_or_none(
                    resolver.functions.text(nameHash, "com.discord").call()
                )
            if "com.reddit" in texts:
                ens.reddit = value_or_none(
                    resolver.functions.text(nameHash, "com.reddit").call()
                )
            if "org.telegram" in texts:
                ens.telegram = value_or_none(
                    resolver.functions.text(nameHash, "org.telegram").call()
                )
        ens_list.append(ens)

    return ens_list


def fetch_from_graph(addresses: List[str]):
    owners = []
    for address in addresses:
        owners.append(address.lower())
    query = f"""query {{
        domains(first: 1000, where: {{owner_in: {json.dumps(owners)}}}) {{
            id
            name
            labelName
            labelhash
            owner {{
            id
            }}
            resolver {{
                texts
                addr {{
                    id
                }}
            }}
        }}
    }}"""
    r = requests.post(ENS_GRAPH_URL, json={"query": query})
    json_data = json.loads(r.text)
    if json_data and json_data["data"]:
        return json_data["data"]["domains"]
    return []


def fetch_twitter_handle(ens_name):
    url = f"https://ethleaderboard.xyz/api/frens?q={ens_name}"
    r = requests.get(url)
    json_data = json.loads(r.text)
    logger.info(f"json_data {json_data}")

    return None
