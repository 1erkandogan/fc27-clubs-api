import json
from typing import Any, Dict, Optional

import pandas as pd
import requests


class FC26APIError(Exception):
    """Represents an error raised while communicating with the FC 26 API."""


class FC26_API:
    """
    Thin client for the EA Sports FC 26 Pro Clubs API.

    The class focuses on defensive request handling while keeping
    DataFrame schemas identical to the upstream API responses.
    """

    BASE_URL = "https://proclubs.ea.com/api/fc"

    def __init__(self, session: Optional[requests.Session] = None, timeout: int = 10) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout
        self.headers: Dict[str, str] = {
            "authority": "proclubs.ea.com",
            "accept-language": "en-US,en;q=0.9",
            "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
            ),
        }
        self._last_error: Optional[FC26APIError] = None

    def _build_url(self, endpoint: str) -> str:
        """Return the full URL for either a relative endpoint or absolute URL."""
        if endpoint.startswith("http"):
            return endpoint
        return f"{self.BASE_URL}/{endpoint.lstrip('/')}"

    def _request_builder(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
        """
        Builds and sends a request to the EA Sports FC 26 Pro Clubs API.

        Args:
            endpoint: The endpoint or absolute URL to send the request to.
            params: The parameters to include in the request.

        Returns:
            A pandas DataFrame containing the response from the API.
        """
        url = self._build_url(endpoint)
        try:
            response = self.session.get(
                url,
                params=params,
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise FC26APIError(f"Request to {url} failed") from exc

        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise FC26APIError(f"Failed to decode JSON from {url}") from exc

        if payload is None:
            return pd.DataFrame()

        return pd.DataFrame(payload)

    def _handle_api_call(self, endpoint: str, params: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """Execute an API call and convert structured errors into None responses."""
        try:
            df = self._request_builder(endpoint, params=params)
            self._last_error = None
            return df
        except FC26APIError as exc:
            self._last_error = exc
            return None

    def _timestamp_to_datetime(self, timestamp: pd.Series, offset_hours: int = 0) -> pd.Series:
        """Convert POSIX timestamps (seconds) into timezone-adjusted datetimes."""
        return pd.to_datetime(timestamp, unit="s") + pd.Timedelta(hours=offset_hours)

    def _apply_timestamp_column(
        self,
        df: pd.DataFrame,
        column_name: str,
        offset_hours: int,
    ) -> pd.DataFrame:
        """Apply timestamp conversion only when the target column exists."""
        if df.empty:
            return df
        if column_name not in df.columns:
            raise FC26APIError(f"Column '{column_name}' not found for timestamp conversion.")
        df = df.copy()
        df[column_name] = self._timestamp_to_datetime(df[column_name], offset_hours=offset_hours)
        return df

    def _normalizer(self, df: Optional[pd.DataFrame], prefix: str) -> Optional[pd.DataFrame]:
        if df is None:
            return None
        if df.empty:
            return df
        if prefix not in df.columns:
            raise FC26APIError(f"Expected nested column '{prefix}' missing from response.")

        nested_series = df[prefix].apply(lambda value: value if isinstance(value, (list, dict)) else {})
        normalized_df = pd.json_normalize(nested_series).add_prefix(prefix)
        final_df = pd.concat([df.drop(columns=[prefix]), normalized_df], axis=1)
        return final_df

    def search_club_by_name(self, club_name: str) -> Optional[pd.DataFrame]:
        """
        Searches for a club by its name.

        Args:
            club_name: The name of the club to search for.

        Returns:
            A pandas DataFrame containing a list of matching clubs, or None if the request fails.
        """
        params = {"platform": "common-gen5", "clubName": club_name}
        clubs = self._handle_api_call("allTimeLeaderboard/search", params=params)
        if clubs is None:
            return None

        try:
            return self._normalizer(clubs, "clubInfo").head(1)
        except FC26APIError as exc:
            self._last_error = exc
            return None

    def get_club_details(self, club_id: str) -> Optional[pd.DataFrame]:
        """
        Retrieves detailed information about a specific club.

        Args:
            club_id: The ID of the club to retrieve information for.

        Returns:
            A pandas DataFrame containing the club's details, or None if the request fails.
        """
        params = {"platform": "common-gen5", "clubIds": club_id}
        club_details = self._handle_api_call("clubs/info", params=params)
        if club_details is None:
            return None
        return club_details.T

    def get_club_matches(self, club_id: str, match_type: str = "friendlyMatch") -> Optional[pd.DataFrame]:
        """
        Retrieve club matches for the provided match type.

        match_type: friendlyMatch, leagueMatch, playoffMatch
        """
        params = {
            "platform": "common-gen5",
            "clubIds": club_id,
            "matchType": match_type,
            "maxResultCount": 10,
        }
        matches = self._handle_api_call("clubs/matches", params=params)
        if matches is None or matches.empty:
            return matches

        try:
            return self._apply_timestamp_column(matches, "timestamp", offset_hours=2)
        except FC26APIError as exc:
            self._last_error = exc
            return None

    def get_club_matches_normalized(
        self,
        club_id: str,
        match_type: str = "friendlyMatch",
        gmt: int = 2,
    ) -> Optional[pd.DataFrame]:
        """
        Retrieve and normalize club matches for the provided match type.

        match_type: friendlyMatch, leagueMatch, playoffMatch
        """
        params = {
            "platform": "common-gen5",
            "clubIds": club_id,
            "matchType": match_type,
            "maxResultCount": 10,
        }
        matches = self._handle_api_call("clubs/matches", params=params)
        if matches is None or matches.empty:
            return matches

        try:
            matches = self._apply_timestamp_column(matches, "timestamp", offset_hours=gmt)
            return self._normalizer(matches, "clubs")
        except FC26APIError as exc:
            self._last_error = exc
            return None


if __name__ == "__main__":
    api = FC26_API()

    # Example 1: Get club details by ID
    # Replace "123456" with a valid club ID
    club_id = "123456"
    club_details = api.get_club_details(club_id)

    if club_details is not None:
        print("\n--- Club Details ---")
        print(club_details)
    else:
        print(f"\n--- No details found for club ID: {club_id} ---")

    # Example 2: Search for a club by name
    # Replace "MyClub" with a valid club name
    club_name = "MyClub"
    search_results = api.search_club_by_name(club_name)

    if search_results is not None:
        print("\n--- Search Results ---")
        print(search_results)
    else:
        print(f"\n--- No clubs found with the name: {club_name} ---")
