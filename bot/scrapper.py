from asyncio import run
from html import escape
from json import dumps
from re import search
from sys import platform

from aiohttp import ClientSession

from bot.exceptions import SummonerNotFound

division_mapping = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}


async def get_build_id():
    print("Refreshing build_id")
    async with ClientSession() as session:
        async with session.get("https://www.op.gg") as resp:
            text = await resp.text()
            print(search(r"buildId\":\"(.*?)\"", text).group(1))
            return search(r"buildId\":\"(.*?)\"", text).group(1)


async def get_rank(summoner: str, build_id: str = None) -> tuple[str, str]:
    async with ClientSession() as session:
        async with session.get(
            f"https://www.op.gg/_next/data/{build_id if build_id else await get_build_id()}/summoners/euw/"
            f"{escape(summoner)}.json?region=euw"
        ) as resp:
            json_response = await resp.json()
            lp_histories = json_response.get("pageProps").get("data").get("lp_histories")
            if lp_histories:
                tier_info: dict[str, str] = lp_histories[0].get("tier_info")
                return summoner, f"{tier_info.get('tier').capitalize()} {tier_info.get('division')}"
            else:
                return summoner, "Gold 4"


async def get_rank_v2(summoner: str, tag: str = "euw") -> tuple[str, str]:
    async with ClientSession() as session:
        async with session.post(
            "https://u.gg/api",
            headers={"Content-Type": "application/json"},
            data=dumps(
                {
                    "operationName": "getSummonerProfile",
                    "variables": {"regionId": "euw1", "riotTagLine": tag, "riotUserName": summoner, "seasonId": 23},
                    "query": "query getSummonerProfile($regionId: String!, $seasonId: Int!, "
                    "$riotUserName: String!, $riotTagLine: String!) {\n  "
                    "fetchProfileRanks(\n    riotUserName: $riotUserName\n    "
                    "riotTagLine: $riotTagLine\n    regionId: $regionId\n    "
                    "seasonId: $seasonId\n  ) {\n    rankScores {\n      "
                    "lastUpdatedAt\n      losses\n      lp\n      "
                    "promoProgress\n      queueType\n      rank\n      role\n      "
                    "seasonId\n      tier\n      wins\n      __typename\n    }\n    "
                    "__typename\n  }\n  profileInitSimple(\n    regionId: $regionId\n   "
                    " riotUserName: $riotUserName\n    riotTagLine: $riotTagLine\n  ) {\n    "
                    "lastModified\n    memberStatus\n    playerInfo {\n      accountIdV3\n      "
                    "accountIdV4\n      exodiaUuid\n      iconId\n      puuidV4\n      regionId\n      "
                    "summonerIdV3\n      summonerIdV4\n      summonerLevel\n      riotUserName\n      "
                    "riotTagLine\n      __typename\n    }\n    customizationData {\n      "
                    "headerBg\n      __typename\n    }\n    __typename\n  }\n}",
                }
            ),
        ) as resp:
            response = await resp.json()
            if response.get("errors"):
                raise SummonerNotFound(summoner, tag)
            tier = response.get("data").get("fetchProfileRanks").get("rankScores")[0].get("tier")
            division = division_mapping.get(
                response.get("data").get("fetchProfileRanks").get("rankScores")[0].get("rank")
            )
            if tier and division:
                return summoner, f"{tier.capitalize()} {division}"
            else:
                return summoner, "Gold 4"


async def get_rank_v3(summoner: str, tag: str = "euw") -> tuple[str, str]:
    async with ClientSession() as session:
        async with session.post(
            "https://mobalytics.gg/api/lol/graphql/v1/query",
            data=dumps(
                {
                    "operationName": "LolSearchQuery",
                    "variables": {"region": "ALL", "text": f"{summoner}#{tag}", "withChampions": False},
                    "extensions": {
                        "persistedQuery": {
                            "version": 1,
                            "sha256Hash": "c0108292df613795e3c6111fedad9abb344eba04b5c2feff1b03cad82550e9cd",
                        }
                    },
                }
            ),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0",
                "Accept": "*/*",
                "Accept-Language": "en_us",
                # 'Accept-Encoding': 'gzip, deflate, br, zstd',
                "Referer": "https://mobalytics.gg/lol",
                "Origin": "https://mobalytics.gg",
                "Connection": "keep-alive",
                # 'Cookie': 'appmobaabgroup=B; appcfcountry=PT; appiscrawler=0',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "no-cors",
                "Sec-Fetch-Site": "same-origin",
                # Requests doesn't support trailers
                # 'TE': 'trailers',
                "content-type": "application/json",
                "x-moba-client": "mobalytics-web",
                "x-moba-proxy-gql-ops-name": "LolSearchQuery",
                "Priority": "u=4",
                "Pragma": "no-cache",
                "Cache-Control": "no-cache",
            },
        ) as resp:
            json = await resp.json()
            try:
                tier = json.get("data").get("search").get("summoners")[0].get("queue").get("tier")
            except AttributeError:
                tier = None
            try:
                division = json.get("data").get("search").get("summoners")[0].get("queue").get("division")
            except AttributeError:
                division = None
            if json.get("data").get("search").get("summoners") is None:
                raise SummonerNotFound(summoner, tag)
            if tier and division:
                return summoner, f"{tier.capitalize()} {division}"
            return summoner, "Gold 4"


if __name__ == "__main__":
    if platform == "win32":
        from asyncio import WindowsSelectorEventLoopPolicy, set_event_loop_policy

        set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    rank = run(get_rank_v3("2n2u", "euw"))
    print(rank)
