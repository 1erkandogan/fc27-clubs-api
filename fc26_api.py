import pandas as pd
import requests
import json

def request_builder(url, params=None):
    headers = {
        "authority": "proclubs.ea.com",
        "accept-language": "en-US,en;q=0.9",
        "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an error if status code is 4xx/5xx
        return pd.DataFrame(response.json())
        
    except requests.exceptions.HTTPError as e:
        print("HTTP error:", e)
    except requests.exceptions.RequestException as e:
        print("Request failed:", e)

def get_club_details(club_id):
    url = "https://proclubs.ea.com/api/fc/clubs/info"
    params = {"platform": "common-gen5", "clubIds": club_id}
    return request_builder(url, params=params)

def search_club_by_name(club_name):
    url = "https://proclubs.ea.com/api/fc/allTimeLeaderboard/search"
    params = {"platform": "common-gen5", "clubName": club_name}

    return request_builder(url, params=params)

if __name__ == "__main__":
    # Example usage
    club_id = "123456"
    club_details = get_club_details(club_id)
    print(club_details)

    club_name = "MyClub"
    search_results = search_club_by_name(club_name)
    print(search_results)