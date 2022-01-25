import re

from bs4 import BeautifulSoup
import cloudscraper


CSGO_STATS_URL = 'https://csgostats.gg/player'
CSGO_STATS_URL_TEMPLATE = 'https://csgostats.gg/player/{steam_id_64}'

def scrape_csgo_gg(steam_id_64):
    url = CSGO_STATS_URL_TEMPLATE.format(steam_id_64=steam_id_64)
    scraper = cloudscraper.create_scraper()
    response = scraper.get(url)
    soup = BeautifulSoup(response.text, features='html.parser')

    # Get rank from badge image src url
    rank_image = soup.select_one('#content-wrapper > div.main-container > div:nth-child(1) > div > div:nth-child(2) > div:nth-child(1) > img')
    rank = re.findall(r'\d+', rank_image.get('src'))[0] if rank_image else None
    
    # Get best rank from badge image src url
    best_rank_image = soup.select_one('#content-wrapper > div.main-container > div:nth-child(1) > div > div:nth-child(2) > div:nth-child(1) > div > img')
    best_rank = re.findall(r'\d+', best_rank_image.get('src'))[0] if best_rank_image else None
    data = {
        'csgo_rank': rank,
        'csgo_best_rank': best_rank,
    }
    return data


if __name__ == '__main__':
    print(scrape_csgo_gg(76561198115900768))