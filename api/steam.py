from dataclasses import dataclass
from datetime import datetime

import requests
import pycountry_convert as pc
from bs4 import BeautifulSoup


STEAMIDIO_URL = 'https://steamid.io/lookup'  # This variable is the name of the website (read the string)


def get_steam_profile_data(steam_profile_url):
    if steam_profile_url_is_valid(steam_profile_url):
        steam_profile_data = scrape_steam_profile(steam_profile_url)
        steamidio_profile_data = scrape_steamidio(steam_profile_url)
        return {**steam_profile_data, **steamidio_profile_data}
    return {}


def steam_profile_url_is_valid(steam_profile_url) -> bool:
    response = requests.get(steam_profile_url)
    return 'The specified profile could not be found.' not in response.text


def scrape_steam_profile(steam_profile_url) -> dict:
    response = requests.get(steam_profile_url)
    soup = BeautifulSoup(response.text, features='html.parser')
    name = soup.select_one('.actual_persona_name').text
    real_name = soup.find('bdi').text
    # Country code needs to have a failsafe in case it doesn't exist
    country_code = soup.select_one('.profile_flag')
    if country_code:
        country_code = country_code['src'][-6:-4].upper()
    # So do each of their subcountries
    country = pc.country_alpha2_to_country_name(country_code) if country_code else None
    continent_code = pc.country_alpha2_to_continent_code(country_code) if country_code else None
    continent = pc.convert_continent_code_to_continent_name(continent_code) if country_code else None
    return {
        'name': name,
        'real_name': real_name,
        'country_code': country_code,
        'country': country,
        'continent_code': continent_code,
        'continent': continent,
    }


def scrape_steamidio(steam_profile_url):
    """Scrape the steamid.io site for a steam user's data."""

    response = requests.post(STEAMIDIO_URL, data={'input': steam_profile_url})
    soup = BeautifulSoup(response.text, features='html.parser')
    data = [item.text.strip('\n').strip() for item in soup.select('dd')]
    steam_id, steam_id_3, steam_id_64, custom_url, profile_state, profile_created, name, location, status, profile = data
    data = {
        'steam_id': steam_id,
        'steam_id_3': steam_id_3,
        'steam_id_64': steam_id_64,
        'custom_url': custom_url,
        'profile_state': profile_state,
        'profile_created': profile_created,
        'name': name,
        'location': location,
        'status': status,
        'profile_url': profile
    }
    return data


@dataclass
class SteamProfile:
    name: str
    real_name: str
    location: str
    profile_created: datetime
    profile_state: str
    profile_url: str
    custom_url: str
    status: str
    steam_id: str
    steam_id_3: str
    steam_id_64: str
    continent: str
    continent_code: str
    country: str
    country_code: str

    @classmethod
    def from_url(cls, steam_profile_url):
        """Create a Steam Profile from a url."""
        steam_profile_data = get_steam_profile_data(steam_profile_url)
        return cls(**steam_profile_data)

    def validate_url(self) -> bool:
        """Checks whether the SteamProfile's current url is valid."""
        return steam_profile_url_is_valid(self.profile_url)


if __name__ == '__main__':
    from pprint import pprint
    zacks_id = 'https://steamcommunity.com/id/zackyp123/'
    alphas_id = 'https://steamcommunity.com/id/spinahpowel/'
    steam_profile = SteamProfile.from_url(zacks_id)
    pprint(steam_profile)