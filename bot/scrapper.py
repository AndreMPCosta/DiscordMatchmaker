from asyncio import run
from html import escape
from re import search
from sys import platform
from aiohttp import ClientSession


async def get_build_id():
    print('Refreshing build_id')
    async with ClientSession() as session:
        async with session.get('https://www.op.gg') as resp:
            text = await resp.text()
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


if __name__ == '__main__':
    if platform == 'win32':
        from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy

        set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    rank = run(get_rank('test'))
    print(rank)
