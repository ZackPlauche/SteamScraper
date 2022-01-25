import unittest

from steam_api.steam import SteamProfile, steam_profile_url_is_valid, get_steam_profile_data

VALID_STEAM_PROFILE_URL = 'https://steamcommunity.com/id/zackyp123'
INVALID_STEAM_PROFILE_URL = 'https://steamcommunity.com/id/zackyp1234'


class TestSteamProfileAPI(unittest.TestCase):

    def test_steam_profile_url_is_valid(self):
        self.assertTrue(steam_profile_url_is_valid(VALID_STEAM_PROFILE_URL))
        self.assertFalse(steam_profile_url_is_valid(INVALID_STEAM_PROFILE_URL))

    def test_get_steam_profile_data(self):
        expected_result = {
            'name': 'SneakAttackZack',
            'real_name': 'Zack Plauche',
            'url': VALID_STEAM_PROFILE_URL,
            'country': 'United States',
            'country_code': 'US',
            'continent': 'North America',
            'continent_code': 'NA',
        }
        self.assertEqual(get_steam_profile_data(VALID_STEAM_PROFILE_URL), expected_result)

    def test_build_steam_profile(self):
        profile = SteamProfile(name='SneakAttackZack', 
                               real_name='Zack Plauche', 
                               url=VALID_STEAM_PROFILE_URL,
                               country='United States',
                               country_code='US',
                               continent='North America',
                               continent_code='NA')
        other_profile = SteamProfile.from_url(VALID_STEAM_PROFILE_URL)
        self.assertEqual(profile, other_profile, 'These two SteamProfiles are not equal.')