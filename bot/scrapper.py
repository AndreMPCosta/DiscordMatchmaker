from asyncio import run
from html import escape
from json import dumps
from re import search
from sys import platform
from aiohttp import ClientSession

division_mapping = {
    'I': 1,
    'II': 2,
    'III': 3,
    'IV': 4,
    'V': 5
}


async def get_build_id():
    print('Refreshing build_id')
    async with ClientSession() as session:
        async with session.get('https://www.op.gg') as resp:
            text = await resp.text()
            print(search(r'buildId\":\"(.*?)\"', text).group(1))
            return search(r'buildId\":\"(.*?)\"', text).group(1)


async def get_rank(summoner: str, build_id: str = None) -> tuple[str, str]:
    async with ClientSession() as session:
        async with session.get(
                f'https://www.op.gg/_next/data/{build_id if build_id else await get_build_id()}/summoners/euw/'
                f'{escape(summoner)}.json?region=euw') as resp:
            json_response = await resp.json()
            lp_histories = json_response.get('pageProps').get('data').get('lp_histories')
            if lp_histories:
                tier_info: dict[str, str] = lp_histories[0].get('tier_info')
                return summoner, f"{tier_info.get('tier').capitalize()} {tier_info.get('division')}"
            else:
                return summoner, 'Gold 4'


async def get_rank_v2(summoner: str, tag: str = "euw") -> tuple[str, str]:
    async with ClientSession() as session:
        async with session.post('https://u.gg/api', headers={
            'Content-Type': 'application/json'
        }, data=dumps({
            "operationName": "getSummonerProfile",
            "variables": {
                "regionId": "euw1",
                "riotTagLine": tag,
                "riotUserName": summoner,
                "seasonId": 23
            },
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
                     "headerBg\n      __typename\n    }\n    __typename\n  }\n}"
        })) as resp:
            response = await resp.json()
            tier = response.get('data').get('fetchProfileRanks').get('rankScores')[0].get('tier')
            division = division_mapping.get(response.get('data').get('fetchProfileRanks').get('rankScores')[0].get('rank'))
            if tier and division:
                return summoner, f"{tier.capitalize()} {division}"
            else:
                return summoner, 'Gold 4'


if __name__ == '__main__':
    if platform == 'win32':
        from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy

        set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    rank = run(get_rank_v2('2n2u', 'euw'))
    print(rank)
