import re
import unicodedata

ROLE_MAP = {
    "top": "TOP",
    "jungle": "JUNGLE",
    "jun": "JUNGLE",
    "jg": "JUNGLE",
    "mid": "MID",
    "middle": "MID",
    "adc": "BOTTOM",
    "ad": "BOTTOM",
    "bot": "BOTTOM",
    "bottom": "BOTTOM",
    "sup": "SUPPORT",
    "support": "SUPPORT",
}

def normalize_name(name: str | None) -> str:
    if not name:
        return ""

    name = unicodedata.normalize("NFKC", name)
    name = name.casefold()

    return re.sub(r"[\W_]+", "", name, flags=re.UNICODE)
    

def normalize_role(role: str | None) -> str | None:
    if not role:
        return None

    return ROLE_MAP.get(role.strip().casefold())

def normalize_country(country: str | None) -> str | None:
    if not country:
        return None

    return country.strip().upper()


def match_player(local_player: dict, candidates: list[dict]):
    nickname = normalize_name(local_player.get("nickname"))
    local_role = normalize_role(local_player.get("main_role"))
    local_country = normalize_country(local_player.get("country_code"))

    matches = []

    for candidate in candidates:
        if normalize_name(candidate.get("name")) != nickname:
            continue

        candidate_role = normalize_role(candidate.get("role"))
        candidate_country = normalize_country(candidate.get("nationality"))

        if (local_role) and (candidate_role) and (local_role != candidate_role):
            continue

        if (local_country) and (candidate_country) and (local_country != candidate_country):
            continue

        matches.append(candidate)

    if len(matches) != 1:
        return None

    result = matches[0]

    role_matches = (
        local_role is not None and local_role == normalize_role(result.get("role"))
    )


## This may be deleted since there are some edge cases for Russian players and also dual citizen players :/
    country_matches = (
        local_country is not None and local_country == normalize_country(result.get("nationality"))
    )

    if not (role_matches or country_matches):
        return None

    return result