import os
import requests
from dotenv import load_dotenv
import datetime

load_dotenv()
api_key_priv = os.getenv('RIOT_API_KEY')

def get_puuid(game_name: str, tagline: str, region: str, api_key: str) -> str:
    api_url = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tagline}?api_key={api_key}"
    resp = requests.get(api_url)
    if resp.status_code != 200:
        raise Exception(f"Error fetching PUUID: {resp.status_code} {resp.text}")

    player_info = resp.json()
    puuid = player_info['puuid']
    return puuid

# here in case changing how often we check
def get_x_match_ids(puuid: str, region: str, api_key: str, count: int) -> list[str]:
    if (count <= 0 or count > 100):
        raise Exception("Invalid count value, must be between 0 and 100")
    api_url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}&api_key={api_key}"
    resp = requests.get(api_url)
    if resp.status_code != 200:
        raise Exception(f"Error fetching match IDs: {resp.status_code} {resp.text}")
    match_ids = resp.json()
    return match_ids

def get_last_match_id(puuid: str, region: str, api_key: str) -> str:
    api_url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=1&api_key={api_key}"
    resp = requests.get(api_url)
    if resp.status_code != 200:
        raise Exception(f"Error fetching match IDs: {resp.status_code} {resp.text}")
    match_id = resp.json()
    return match_id[0]

def get_match_data(match_id: str, region: str, api_key: str) -> dict:
    api_url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={api_key}"
    resp = requests.get(api_url)
    if resp.status_code != 200:
        raise Exception(f"Error fetching match data: {resp.status_code} {resp.text}")
    match_data = resp.json()
    return match_data

def get_participant_number(match_data: dict, puuid: str) -> int:
    return match_data['metadata']['participants'].index(puuid)

def get_participant_data(match_data: dict, participant_number: int) -> dict:
    return match_data['info']['participants'][participant_number]

def get_timestamp(match_data: dict) -> datetime.datetime:
    start = match_data['info']['gameStartTimestamp']
    duration = match_data['info']['participants'][0]['timePlayed']
    timestamp = (start + duration) / 1000
    return datetime.datetime.fromtimestamp(timestamp)

def get_kda(participant_data: dict) -> float:
    kills =  participant_data['kills']
    assists = participant_data['assists']
    deaths = participant_data['deaths']
    if deaths == 0:
        deaths = 1
    return (kills + assists) / deaths

def get_kda_from_names(game_name: str, tagline: str, region: str, api_key: str) -> float:
    puuid = get_puuid(game_name, tagline, region, api_key)
    match_ids = get_x_match_ids(puuid, region, api_key, 1)
    match_data = get_match_data(match_ids[0], region, api_key)
    participant_number = get_participant_number(match_data, puuid)
    participant_data = get_participant_data(match_data, participant_number)
    return get_kda(participant_data)


def get_all_from_names(game_name: str, tagline: str, region: str, api_key: str) -> dict:
    puuid = get_puuid(game_name, tagline, region, api_key)
    match_id = get_last_match_id(puuid, region, api_key)
    match_data = get_match_data(match_id, region, api_key)
    participant_number = get_participant_number(match_data, puuid)
    participant_data = get_participant_data(match_data, participant_number)
    kda = get_kda(participant_data)
    timestamp = get_timestamp(match_data)
    return {"match_id": match_id, "timestamp": timestamp, "kda": kda}

#small test
'''
game_name = input("Enter game name: ")
tagline = input("Enter tagline: ")
region = input("Enter region: ")
#puuid = get_puuid(game_name, tagline, region, api_key_priv)
#mid = get_last_match_id(puuid, region, api_key_priv)
kda = get_kda_from_names(game_name, tagline, region, api_key_priv)
print(f"Your latest KDA is: {kda}")
#print(f"Your latest MatchID is: {mid}")
'''

