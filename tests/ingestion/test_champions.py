import cv2

from bot import get_project_root
from bot.ingestion.match import ImageRecognition

correct_guesses = [
    ["Jhin", "Akali", "Karma", "MasterYi", "Zyra", "Olaf", "Quinn", "Annie", "LeeSin", "Sona"],
    ["Kaisa", "Akali", "Amumu", "Sylas", "Nami", "Sett", "JarvanIV", "Ahri", "Yasuo", "Singed"],
    ["Yasuo", "Draven", "Lux", "Fiddlesticks", "Ezreal", "Syndra", "MissFortune", "Volibear", "Leblanc", "Lucian"],
    ["Kaisa", "Akali", "Amumu", "Sylas", "Nami", "Sett", "JarvanIV", "Ahri", "Yasuo", "Singed"],
    ["Ashe", "Vex", "Yorick", "Thresh", "Kindred", "Senna", "Rumble", "Jhin", "Sejuani", "Renekton"],
    ["Vladimir", "Volibear", "Viego", "Kaisa", "Thresh", "Gwen", "Udyr", "Yone", "Jinx", "Seraphine"],
    ["Shaco", "MissFortune", "Leona", "Swain", "Yorick", "Caitlyn", "Skarner", "Blitzcrank", "Teemo", "Heimerdinger"],
    ["Vladimir", "Nautilus", "Udyr", "MissFortune", "Yone", "KSante", "Blitzcrank", "Morgana", "Vayne", "Lissandra"],
    ["Talon", "Shyvana", "Seraphine", "Caitlyn", "Renekton", "Diana", "Jhin", "Yone", "Sejuani", "Nautilus"],
    ["Gragas", "Thresh", "Khazix", "Yasuo", "Kaisa", "Lux", "Blitzcrank", "Caitlyn", "Lillia", "Wukong"],
    ["Yasuo", "Zac", "Zeri", "Nami", "Gwen", "Smolder", "KSante", "Veigar", "Nautilus", "Graves"],
    ["Kayle", "Udyr", "Kaisa", "Sylas", "Thresh", "Ekko", "Rumble", "Ashe", "Kayn", "Morgana"],
    ["Kayle", "JarvanIV", "MissFortune", "Blitzcrank", "Yone", "Ekko", "Yorick", "Ashe", "Brand", "Senna"],
]

debug = False


def test_guess_champions_1():
    img_recognition = ImageRecognition(debug=debug)
    img_recognition.set_screenshot(cv2.imread(f"{get_project_root()}/tests/data/test1.png"))
    champions = img_recognition.get_champions()
    print(champions)
    assert champions == correct_guesses[0]


def test_guess_champions_2():
    img_recognition = ImageRecognition(debug=debug)
    img_recognition.set_screenshot(cv2.imread(f"{get_project_root()}/tests/data/test2.png"))
    champions = img_recognition.get_champions()
    print(champions)
    assert champions == correct_guesses[1]


def test_guess_champions_3():
    img_recognition = ImageRecognition(debug=debug)
    img_recognition.set_screenshot(cv2.imread(f"{get_project_root()}/tests/data/test3.png"))
    champions = img_recognition.get_champions()
    print(champions)
    assert champions == correct_guesses[2]


def test_guess_champions_4():
    img_recognition = ImageRecognition(debug=debug)
    img_recognition.set_screenshot(cv2.imread(f"{get_project_root()}/tests/data/test4_bigger.png"))
    champions = img_recognition.get_champions()
    print(champions)
    assert champions == correct_guesses[3]


def test_guess_champions_5():
    img_recognition = ImageRecognition(debug=debug)
    img_recognition.set_screenshot(cv2.imread(f"{get_project_root()}/tests/data/test5.png"))
    champions = img_recognition.get_champions()
    print(champions)
    assert champions == correct_guesses[4]


def test_guess_champions_6():
    img_recognition = ImageRecognition(debug=debug)
    img_recognition.set_screenshot(cv2.imread(f"{get_project_root()}/tests/data/test6.png"))
    champions = img_recognition.get_champions()
    print(champions)
    assert champions == correct_guesses[5]


def test_guess_champions_7():
    img_recognition = ImageRecognition(debug=debug)
    img_recognition.set_screenshot(cv2.imread(f"{get_project_root()}/tests/data/test7.png"))
    champions = img_recognition.get_champions()
    print(champions)
    assert champions == correct_guesses[6]


def test_guess_champions_8():
    img_recognition = ImageRecognition(debug=debug)
    img_recognition.set_screenshot(cv2.imread(f"{get_project_root()}/tests/data/test8.png"))
    champions = img_recognition.get_champions()
    print(champions)
    assert champions == correct_guesses[7]


def test_guess_champions_9():
    img_recognition = ImageRecognition(debug=debug)
    img_recognition.set_screenshot(cv2.imread(f"{get_project_root()}/tests/data/test9.png"))
    champions = img_recognition.get_champions()
    print(champions)
    assert champions == correct_guesses[8]


def test_guess_champions_10():
    img_recognition = ImageRecognition(debug=debug)
    img_recognition.set_screenshot(cv2.imread(f"{get_project_root()}/tests/data/test10.png"))
    champions = img_recognition.get_champions()
    print(champions)
    assert champions == correct_guesses[9]


def test_guess_champions_11():
    img_recognition = ImageRecognition(debug=debug)
    img_recognition.set_screenshot(cv2.imread(f"{get_project_root()}/tests/data/test11.png"))
    champions = img_recognition.get_champions()
    print(champions)
    assert champions == correct_guesses[10]


def test_guess_champions_12():
    img_recognition = ImageRecognition(debug=debug)
    img_recognition.set_screenshot(cv2.imread(f"{get_project_root()}/tests/data/test12.png"))
    champions = img_recognition.get_champions()
    print(champions)
    assert champions == correct_guesses[11]


def test_guess_champions_13():
    img_recognition = ImageRecognition(debug=debug)
    img_recognition.set_screenshot(cv2.imread(f"{get_project_root()}/tests/data/test13.png"))
    champions = img_recognition.get_champions()
    print(champions)
    assert champions == correct_guesses[12]
