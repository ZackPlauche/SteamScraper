from dataclasses import dataclass
import time
from datetime import datetime

import asyncio
from bs4 import BeautifulSoup
from pyppeteer import launch

FACEITFINDER_URL = 'https://faceitfinder.com/'
VALID_FACEITFINDER_PROFILE_URL = 'https://faceitfinder.com/profile/76561197974402593'
VALID_STEAM_PROFILE_URL = 'https://steamcommunity.com/id/Omega_1001/'


def get_faceit_data(steam_profile_url: str) -> dict:
    """Get all available data from a faceitfinder search."""
    faceitfinder_page = get_faceitfinder_page(steam_profile_url)
    if faceitfinder_page_is_valid(faceitfinder_page):
        soup = BeautifulSoup(faceitfinder_page, features="html.parser")
        steam_name = soup.select_one('.account-steam-name').span.text
        faceit_list_data = [li.span.text for li in  soup.find_all('li')]
        steam_data = faceit_list_data[:2]
        steam_account_status, steam_account_created = steam_data
        csgo_data = faceit_list_data[2:]
        plays_csgo_since, csgo_total_hours, csgo_last_2_weeks_hours, csgo_achievements, csgo_banned_friends = csgo_data
        csgo_username = soup.select_one('.account-faceit-title-username').text
        csgo_skill_level = soup.select_one('.account-faceit-level').img['src'][-8]
        csgo_stats = [stat.strong.text for stat in soup.select('.account-faceit-stats-single')]
        csgo_matches, csgo_elo, csgo_kd, csgo_win_rate, csgo_wins, csgo_hs = csgo_stats
        return {
            'steam_name': steam_name,
            'steam_account_status': steam_account_status,
            'steam_account_created': steam_account_created,
            'plays_csgo_since': plays_csgo_since,
            'csgo_total_hours': csgo_total_hours,
            'csgo_last_2_weeks_hours': csgo_last_2_weeks_hours,
            'csgo_achievements': csgo_achievements,
            'csgo_banned_friends': csgo_banned_friends,
            'csgo_username': csgo_username,
            'csgo_skill_level': csgo_skill_level, 
            'csgo_matches': csgo_matches,
            'csgo_elo': csgo_elo,
            'csgo_kd': csgo_kd,
            'csgo_win_rate': csgo_win_rate,
            'csgo_wins': csgo_wins,
            'csgo_hs': csgo_hs,
        }



@dataclass
class FaceitProfile:

    def __init__(
        self, 
        steam_name, 
        steam_account_status,
        steam_account_created, 
        plays_csgo_since,
        csgo_total_hours, 
        csgo_last_2_weeks_hours,
        csgo_achievements,
        csgo_banned_friends,
        csgo_username,
        csgo_skill_level,
        csgo_matches,
        csgo_elo,
        csgo_kd,
        csgo_win_rate,
        csgo_wins,
        csgo_hs
    ):
        self.steam_name = steam_name
        self.steam_account_status = steam_account_status
        self.steam_account_created = parse_faceit_datetime(steam_account_created) # Datetime Steam account was created
        self.plays_csgo_since = parse_faceit_datetime(plays_csgo_since) # Datetime Steam account was created
        self.csgo_total_hours = float(csgo_total_hours)
        self.csgo_last_2_weeks_hours = float(csgo_last_2_weeks_hours)
        self.csgo_achivements = csgo_achievements
        self.csgo_banned_friends = csgo_banned_friends
        self.csgo_username = csgo_username
        self.csgo_skill_level = int(csgo_skill_level)
        self.csgo_matches = int(csgo_matches)
        self.csgo_elo = int(csgo_elo)
        self.csgo_kd = float(csgo_kd)
        self.csgo_win_rate = csgo_win_rate
        self.csgo_wins = int(csgo_wins)
        self.csgo_hs = csgo_hs

    @classmethod
    def from_url(cls, steam_profile_url: str):
        faceit_data = get_faceit_data(steam_profile_url)
        return cls(**faceit_data)


def parse_faceit_datetime(string):
    # Faceit time format: DD.MM.YYYY
    return datetime.strptime(string, '%d.%m.%Y')



def get_faceitfinder_page(steam_profile_url: str) -> str:
    """
    Gets a Steam User's Faceit Profile Page from Faceitfinder.com and 
    returns the html for it.
    """

    async def async_wrapper(steam_profile_url):
        browser = await launch(headless=True, defaultViewport=None)
        page = (await browser.pages())[0]
        await page.goto(FACEITFINDER_URL)
        await page.type('.menu-input', steam_profile_url)
        await page.click('#searchButton')
        await page.waitForSelector('.account-row')  # TODO: Add way to check for 'Players not found!' page.
        html = await page.content()
        await browser.close()
        return html
    html = asyncio.run(async_wrapper(steam_profile_url))
    return html


def faceitfinder_page_is_valid(faceitfinder_page_html: str) -> bool:
    """
    Checks if the 'Player not found!' text is found on a faceitfinder page's html.
    This is only found on the page of a failed steam profile search.
    """

    return 'Players not found!'not in faceitfinder_page_html


if __name__ == '__main__':
    start = time.time()
    data = get_faceit_data(VALID_STEAM_PROFILE_URL)
    end = time.time()
    from pprint import pprint
    pprint(data)
    print(f'Time: {end - start}')