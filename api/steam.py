import requests
from bs4 import BeautifulSoup

BASE_URL = 'https://steamcommunity.com/id/'


class SteamProfile:

    def __init__(self, name, real_name, url=None):
        self.name = name
        self.real_name = real_name
        self.url = url

    @classmethod
    def from_url(cls, steam_profile_url):
        response = requests.get(steam_profile_url)
        soup = BeautifulSoup(response.text, features='html.parser')

        name = soup.find('span', {'class': 'actual_persona_name'}).text
        real_name = soup.find('bdi').text
        url = steam_profile_url
        return cls(name, real_name, url)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"SteamProfile(name={repr(self.name)}, real_name={repr(self.real_name)}, url={repr(self.url)})"

    def validate_url(self) -> bool:
        response = requests.get(self.url + '1')
        # The text 'The specified profile could not be found' occurs when a steam profile isn't found.
        return 'The specified profile could not be found.' in response.text


if __name__ == '__main__':
    profile = SteamProfile.from_url('https://steamcommunity.com/id/zackyp123')
    print(profile.validate_url())
