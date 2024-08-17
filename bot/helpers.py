from asyncio import gather
from copy import deepcopy
from random import randint, sample

from discord import utils

from bot.consts import points, threshold
from bot.scrapper import get_rank_v2


async def draw(
    mid_point: float, list_ranked_summoners: list[tuple[str, int]]
) -> tuple[dict[str, int | list], dict[str, int | list]]:
    blue_team = {"score": 0, "players": []}
    while blue_team["score"] < mid_point:
        random_index = randint(0, len(list_ranked_summoners) - 1)
        random_summoner = list_ranked_summoners[random_index]
        blue_team["players"].append(random_summoner[0])
        blue_team["score"] += random_summoner[1]
        list_ranked_summoners.pop(random_index)
        if len(blue_team.get("players")) == 4:
            comparison_value = mid_point - blue_team["score"]
            elected_summoner = 0
            min_value = abs(list_ranked_summoners[0][1] - comparison_value)
            for j in range(0, len(list_ranked_summoners) - 1):
                if abs(list_ranked_summoners[j][1] - comparison_value) < min_value:
                    elected_summoner = j
                    min_value = abs(list_ranked_summoners[j][1] - comparison_value)
            blue_team["players"].append(list_ranked_summoners[elected_summoner][0])
            blue_team["score"] += list_ranked_summoners[elected_summoner][1]
            list_ranked_summoners.pop(elected_summoner)
            break
        if len(blue_team["players"]) == 5:
            break
    red_team = {
        "score": mid_point * 2 - blue_team.get("score"),
        "players": [summoner[0] for summoner in list_ranked_summoners],
    }
    return blue_team, red_team


async def balance(
    summoners: list[tuple[str, str]],
) -> tuple[dict[str, int | list], dict[str, int | list], dict[str, str]]:
    tasks = []
    mid_point = 0
    draws = 0
    for summoner, tag in summoners:
        tasks.append(get_rank_v2(summoner, tag))
    results = await gather(*tasks)
    summoners = [summoner[0] for summoner in summoners]
    mapped_results = {result[0]: result[1] for result in results}
    shuffled_summoners = sample(summoners, 10)
    ranked_summoners = {summoner: points.get(mapped_results.get(summoner)) for summoner in shuffled_summoners}
    for summoner, evaluation in ranked_summoners.items():
        mid_point += evaluation
    mid_point /= 2
    list_ranked_summoners = list(ranked_summoners.items())
    blue_team, red_team = await draw(mid_point, deepcopy(list_ranked_summoners))
    draws += 1
    initial_threshold = threshold
    while abs(blue_team.get("score") - red_team.get("score")) > initial_threshold:
        blue_team, red_team = await draw(mid_point, deepcopy(list_ranked_summoners))
        draws += 1
        if draws >= 1000:
            initial_threshold += 1
    return blue_team, red_team, mapped_results


def beautify_teams(
    blue_team: dict[str, int | list], red_team: dict[str, int | list], ranks: dict[str, str], emojis=None
):
    def helper_formatting(out, player=None, _emojis=None):
        try:
            if emojis:
                out += "{}. {} {}\n".format(
                    player[0], player[1], (utils.get(emojis, name=ranks.get(player[1]).split()[0].capitalize()))
                )
            else:
                out += "{}. {} {}\n".format(player[0], player[1], (ranks.get(player[1]).split()[0]))
        except (Exception,):
            return f"{player[0]}. {player[1]} -> There was a problem processing the rank"
        return out

    output_string = "Game: Closed\n"
    output_string += "```ini\n" "[Blue Team with Score: {0:.2f}]\n" "```".format(blue_team["score"])
    x_blue_team = enumerate(blue_team["players"], start=1)
    x_red_team = enumerate(red_team["players"], start=6)
    for p in x_blue_team:
        output_string = helper_formatting(output_string, player=p, _emojis=emojis)

    output_string += "```ansi\n" "\x1b[2;31m[Red Team with Score: {0:.2f}]\x1b[0m\x1b[2;31m\x1b[0m\n" "```".format(
        red_team["score"]
    )

    for p in x_red_team:
        output_string = helper_formatting(output_string, player=p, _emojis=emojis)

    output_string += "```css\n" "[Average Score: {0:.2f}]\n" "```".format((red_team["score"] + blue_team["score"]) / 2)
    return output_string
