from bs4 import BeautifulSoup
import requests
import bs4

FACEIT_PROFILE_SEARCH_URL = 'https://faceitfinder.com/'
FACEIT_PROFILE_SEARCH_URL_WITH_PARAMS = 'https://faceitfinder.com/profile/'
VALID_FACEIT_PROFILE_SEARCH_URL = 'https://faceitfinder.com/profile/76561197974402593'

def get_faceit_data_form_steam_profile_url(url):
    # headers needed to use 
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    }
    response = requests.get(url, headers=headers)
    html = BeautifulSoup(response.text, features="html.parser")
    return html



if __name__ == '__main__':
    html = get_faceit_data_form_steam_profile_url(VALID_FACEIT_PROFILE_SEARCH_URL)
    print(html)