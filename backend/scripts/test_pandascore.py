import os
import httpx
from dotenv import load_dotenv
from api.services.pandascore_client import PandaScoreClient

load_dotenv()

client = PandaScoreClient()

try:
    players = client.get_players(per_page=3)

    for player in players:
        print(player["name"], "-", player.get("role"))
finally:
    client.close()