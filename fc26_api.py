import pandas as pd
import requests
import json

def request_builder(url, params=None):
    """
    Builds and sends a request to the EA Sports FC 26 Pro Clubs API.

    Args:
        url: The URL to send the request to.
        params: The parameters to include in the request.

    Returns:
        A pandas DataFrame containing the response from the API, or None if the request fails.
    """
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
        print(f"HTTP error: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {e}")
        return None

def get_club_details(club_id: str) -> Optional[pd.DataFrame]:
    """
    Retrieves detailed information about a specific club.

    Args:
        club_id: The ID of the club to retrieve information for.

    Returns:
        A pandas DataFrame containing the club's details, or None if the request fails.
    """
    url = "https://proclubs.ea.com/api/fc/clubs/info"
    params = {"platform": "common-gen5", "clubIds": club_id}
    return request_builder(url, params=params)

def search_club_by_name(club_name: str) -> Optional[pd.DataFrame]:
    """
    Searches for a club by its name.

    Args:
        club_name: The name of the club to search for.

    Returns:
        A pandas DataFrame containing a list of matching clubs, or None if the request fails.
    """
    url = "https://proclubs.ea.com/api/fc/allTimeLeaderboard/search"
    params = {"platform": "common-gen5", "clubName": club_name}
    return request_builder(url, params=params)

if __name__ == "__main__":
    # Example 1: Get club details by ID
    # Replace "123456" with a valid club ID
    club_id = "123456"
    club_details = get_club_details(club_id)

    if club_details is not None:
        print("\n--- Club Details ---")
        print(club_details)
    else:
        print(f"\n--- No details found for club ID: {club_id} ---")

    # Example 2: Search for a club by name
    # Replace "MyClub" with a valid club name
    club_name = "MyClub"
    search_results = search_club_by_name(club_name)

    if search_results is not None:
        print("\n--- Search Results ---")
        print(search_results)
    else:
        print(f"\n--- No clubs found with the name: {club_name} ---")