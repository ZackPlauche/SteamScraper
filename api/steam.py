from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

BASE_URL = 'https://steamcommunity.com/id/'


def get_steam_profile_data(url):
    """Collects data from a Steam Profile public page."""

    response = requests.get(url)
    html = BeautifulSoup(response.text)
    name = html.find('span', {'class': 'actual_persona_name'}).text
    real_name = html.find('bdi').text
    data = {
        'name': name,
        'real_name': real_name,
        'url': url
    }
    return data


def steam_profile_url_is_valid(url) -> bool:
    """Checks if a Steam Profile url is valid. Returns a Boolean"""
    response = requests.get(url)
    steam_error_message = 'The specified profile could not be found.' 
    url_is_valid = steam_error_message not in response.text
    return url_is_valid


@dataclass
class SteamProfile:
    name: str
    real_name: str
    url: str = None

    def __str__(self):
        return self.name

    @classmethod
    def from_url(cls, steam_profile_url):
        """Create a Steam Profile from a url."""
        if steam_profile_url_is_valid(steam_profile_url): 
            steam_profile_data = get_steam_profile_data(steam_profile_url)
            print(steam_profile_data)
            return cls(**steam_profile_data)

    def validate_url(self) -> bool:
        """Checks whether the SteamProfile's current url is valid."""
        return steam_profile_url_is_valid(self.url)