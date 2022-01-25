import re

import requests
from bs4 import BeautifulSoup

FACEITFINDER_URL = 'https://faceitfinder.com/'
FACEITFINDER_URL_TEMPLATE = 'https://faceitfinder.com/profile/{steam_id_64}'


def scrape_faceitfinder(steam_id_64):
    data = {}
    url = FACEITFINDER_URL_TEMPLATE.format(steam_id_64=steam_id_64)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200 and faceitfinder_page_is_valid(response.text):
        soup = BeautifulSoup(response.text, features='html.parser')
        # steam_name = soup.select_one('.account-steam-name').span.text
        faceit_list_values = [li.span.text for li in  soup.find_all('li')]
        csgo_username = soup.select_one('.account-faceit-title-username')
        csgo_skill_level = soup.select_one('.account-faceit-level')
        csgo_stats = [stat.strong.text for stat in soup.select('.account-faceit-stats-single')]
        faceit_data = {
            # Anything commented out is something we already get from the Steam scraper
            # 'steam_name': steam_name,
            # 'steam_account_status': faceit_list_values[0],
            # 'steam_account_created': faceit_list_values[1],
            'csgo_plays_since': faceit_list_values[2],
            'csgo_total_hours': faceit_list_values[3],
            'csgo_last_2_weeks_hours': faceit_list_values[4],
            'csgo_achievements': faceit_list_values[5],
            'csgo_banned_friends': faceit_list_values[6],
            'csgo_username': csgo_username.text,
            'faceit_skill_level': re.findall(r'\d+', csgo_skill_level.img.get('src'))[0] if csgo_username else None,
            'csgo_matches': csgo_stats[0] if csgo_stats else None,
            'csgo_elo': csgo_stats[1] if csgo_stats else None,
            'csgo_kd': csgo_stats[2] if csgo_stats else None,
            'csgo_win_rate': csgo_stats[3] if csgo_stats else None,
            'csgo_wins': csgo_stats[4] if csgo_stats else None,
            'csgo_hs': csgo_stats[5] if csgo_stats else None,
        }
        data.update(faceit_data)
    return data



def faceitfinder_page_is_valid(faceitfinder_page_html: str) -> bool:
    """
    Checks if the 'Player not found!' text is found on a faceitfinder page's html.
    This is only found on the page of a failed steam profile search.
    """

    return 'Players not found!'not in faceitfinder_page_html