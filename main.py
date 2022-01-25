from steam_api import SteamProfile

profile = SteamProfile.from_url('https://steamcommunity.com/id/omega_1001/')
print(vars(profile))