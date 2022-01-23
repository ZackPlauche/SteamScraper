from dataclasses import dataclass

import pycountry_convert as pc
import requests
from bs4 import BeautifulSoup

BASE_URL = 'https://steamcommunity.com/id/'


def get_steam_profile_data(steam_profile_url):
    """Collects data from a Steam Profile public page."""

    if steam_profile_url_is_valid(steam_profile_url): 
        response = requests.get(steam_profile_url)
        soup = BeautifulSoup(response.text, features='html.parser')
        name = soup.select_one('.actual_persona_name').text
        real_name = soup.find('bdi').text
        country_code = soup.select_one('.profile_flag')['src'][-6:-4].upper()
        country = pc.country_alpha2_to_country_name(country_code)
        continent_code = pc.country_alpha2_to_continent_code(country_code)
        continent = pc.convert_continent_code_to_continent_name(continent_code)
        data =  {
            'name': name,
            'real_name': real_name,
            'url': steam_profile_url,
            'country_code': country_code,
            'country': country,
            'continent_code': continent_code,
            'continent': continent,
        }
        return data


def steam_profile_url_is_valid(steam_profile_url) -> bool:
    """Checks if a Steam Profile url is valid. Returns a Boolean"""

    response = requests.get(steam_profile_url)
    steam_error_message = 'The specified profile could not be found.' 
    url_is_valid = steam_error_message not in response.text
    return url_is_valid


@dataclass
class SteamProfile:

    def __init__(self, name, real_name, url, country, country_code, continent, continent_code):
        self.name = name
        self.real_name = real_name,
        self.url = url
        self.country = country
        self.country_code = country_code
        self.continent = continent
        self.continent_code = continent_code

    @classmethod
    def from_url(cls, steam_profile_url):
        """Create a Steam Profile from a url."""
        steam_profile_data = get_steam_profile_data(steam_profile_url)
        return cls(**steam_profile_data)

    def validate_url(self) -> bool:
        """Checks whether the SteamProfile's current url is valid."""
        return steam_profile_url_is_valid(self.url)


if __name__ == '__main__':
    from pprint import pprint
    output_data = get_steam_profile_data('https://steamcommunity.com/id/spinahpowel/')
    pprint(output_data)