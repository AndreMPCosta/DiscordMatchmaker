from unicodedata import combining, normalize


def remove_accents(input_str):
    normalized_string = normalize("NFKD", input_str)
    return "".join([c for c in normalized_string if not combining(c)])


if __name__ == "__main__":
    print(remove_accents("áéíóú"))
    print(remove_accents("àèìòù"))
    print(remove_accents("âêîôû"))
    print(remove_accents("äëïöü"))
    print(remove_accents("ç"))
    print(remove_accents("ñ"))
    print(remove_accents("ÁÉÍÓÚ"))
    print(remove_accents("ÀÈÌÒÙ"))
    print(remove_accents("ÂÊÎÔÛ"))
    print(remove_accents("ÄËÏÖÜ"))
    print(remove_accents("Ç"))
    print(remove_accents("Ñ"))
    print(remove_accents("ãõ"))
    print(remove_accents("ÃÕ"))
    print(remove_accents("ß"))
    print(remove_accents("ÿ"))
    print(remove_accents("Ø"))
    print(remove_accents("ø"))
    print(remove_accents("œ"))
    print(remove_accents("Œ"))
    print(remove_accents("æ"))
    print(remove_accents("Æ"))
    print(remove_accents("å"))
    print(remove_accents("Å"))
    print(remove_accents("Þ"))
    print(remove_accents("þ"))
    print(remove_accents("ð"))
    print(remove_accents("Ð"))
