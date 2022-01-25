import time
from steam_api import SteamProfile
from pprint import pprint

start = time.time()
profile = SteamProfile.from_url('https://steamcommunity.com/id/omega_1001/')
end = time.time()
print(end - start)
pprint(vars(profile))