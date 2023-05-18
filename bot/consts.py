from os.path import normpath

from bot import get_project_root

points = {
    'Challenger': 200,
    'CHALLENGER': 200,
    'Grandmaster': 175,
    'GRANDMASTER': 175,
    'Master': 155,
    'MASTER': 155,
    'DIAMOND I': 145,
    'DIAMOND II': 140,
    'DIAMOND III': 135,
    'DIAMOND IV': 130,
    'Diamond 1': 145,
    'Diamond 2': 140,
    'Diamond 3': 135,
    'Diamond 4': 130,
    'PLATINUM I': 120,
    'PLATINUM II': 115,
    'PLATINUM III': 110,
    'PLATINUM IV': 105,
    'Platinum 1': 120,
    'Platinum 2': 115,
    'Platinum 3': 110,
    'Platinum 4': 105,
    'GOLD I': 95,
    'GOLD II': 90,
    'GOLD III': 85,
    'GOLD IV': 80,
    'Gold 1': 95,
    'Gold 2': 90,
    'Gold 3': 85,
    'Gold 4': 80,
    'SILVER I': 70,
    'SILVER II': 65,
    'SILVER III': 60,
    'SILVER IV': 55,
    'Silver 1': 70,
    'Silver 2': 65,
    'Silver 3': 60,
    'Silver 4': 55,
    'BRONZE I': 45,
    'BRONZE II': 40,
    'BRONZE III': 35,
    'BRONZE IV': 30,
    'Bronze 1': 45,
    'Bronze 2': 40,
    'Bronze 3': 35,
    'Bronze 4': 30,
    'IRON I': 20,
    'IRON II': 15,
    'IRON III': 10,
    'IRON IV': 5,
    'Iron 1': 20,
    'Iron 2': 15,
    'Iron 3': 10,
    'Iron 4': 5,
    'Unranked': 0,
    'UNRANKED': 0,
    '\n\t\t\tUnranked\n\t\t': 0
}

data_folder = normpath(f'{get_project_root()}/data')

threshold = 5  # max number of points of difference between teams

refresh_interval = 600  # in seconds
