import os, sys, linecache, io, subprocess
from PIL import Image
from os import path
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.ui import Select
from socket import *
from datetime import *
from time import sleep

def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))

def get_chromedriver(use_proxy=True, user_agent=None):
    chrome_options = Options()
    chrome_service = Service(os.path.abspath(os.getcwd()) + '/chromedriver')
    chrome_options.add_argument('--window-size=700,500')
    chrome_options.add_argument('--incognito')
    chrome_options.add_argument('--headless')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    driver = Chrome(service=chrome_service, options=chrome_options)
    return driver

class SteamID64:
    def __init__(self, driver, steam_link):
        self.url = 'https://steamid.io/lookup'
        self.steam_link = steam_link
        self.steam_input_path = '/html/body/div/div[1]/form/div/input'
        self.steam_lookup_path = '/html/body/div/div[1]/form/div/div/button[2]'
        self.steam_id_path = '/html/body/div/div[2]/div[2]/section/dl/dd[3]/a'
        self.driver = driver
        self.driver.get(self.url)

    def fetch_info(self):
        try:
            WebDriverWait(self.driver, 50).until(EC.presence_of_element_located((By.XPATH, self.steam_input_path)))
            sleep(0.3)
            self.driver.find_element(By.XPATH, self.steam_input_path).send_keys(self.steam_link)
            WebDriverWait(self.driver, 50).until(EC.presence_of_element_located((By.XPATH, self.steam_lookup_path)))
            sleep(0.3)
            self.driver.find_element(By.XPATH, self.steam_lookup_path).click()
            WebDriverWait(self.driver, 50).until(EC.presence_of_element_located((By.XPATH, self.steam_id_path)))
            sleep(0.3)
            return self.driver.find_element(By.XPATH, self.steam_id_path).text
        except:
            PrintException()

class Faceit:
    def __init__(self, driver, steam_id):
        self.url = 'https://www.faceit.com/en/'
        self.steam_id = steam_id
        self.faceit_search_path = '/html/body/div[2]/logged-out-header/div/div[1]/div/div[2]/div[2]/div'
        self.faceit_input_path = '/html/body/div[2]/logged-out-header/div/div[1]/div/div[2]/div[2]/div/div[1]/input'
        self.level_path = 'body > div:nth-child(3) > logged-out-header > div > div.sc-kkJYca.cPmIai > div > div.sc-bXoPdI.esuYfd > div.sc-cbpyHp.sc-hJaIcF.ggtNQi.cejILD > div > div.sc-ghqynf.gKsJPc > div > div:nth-child(2) > div:nth-child(2) > div > div > div:nth-child(2) > div > svg'
        self.profile_path = '/html/body/div[2]/logged-out-header/div/div[1]/div/div[2]/div[2]/div/div[4]/div/div[2]/div[2]/div/div'
        self.profile_pfp_path = '/html/body/div[2]/logged-out-header/div/div[1]/div/div[2]/div[2]/div/div[4]/div/div[2]/div[2]/div/div/div[1]/div[1]/img'
        self.driver = driver
        size = self.driver.get_window_size()
        self.size_x = int(size['width'])
        self.size_y = int(size['height'])
        self.driver.get(self.url)

    def fetch_info(self):
        try:
            WebDriverWait(self.driver, 50).until(EC.presence_of_element_located((By.XPATH, self.faceit_search_path)))
            sleep(0.3)
            while True:
                try:
                    self.driver.find_element(By.XPATH, self.faceit_search_path).click()
                    break
                except:
                    self.size_x += 50
                    self.size_y += 10
                    self.driver.set_window_size(self.size_x, self.size_y)
            element = WebDriverWait(self.driver, 50).until(EC.presence_of_element_located((By.XPATH, self.faceit_input_path)))
            sleep(0.3)
            element.send_keys(self.steam_id)
            sleep(0.3)
            element = WebDriverWait(self.driver, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, self.level_path)))
            sleep(0.3)
            lvl_image = io.BytesIO(element.screenshot_as_png)
            element = WebDriverWait(self.driver, 50).until(EC.presence_of_element_located((By.XPATH, self.profile_pfp_path)))
            sleep(0.3)
            pfp_image = element.get_attribute("src")
            element = WebDriverWait(self.driver, 50).until(EC.presence_of_element_located((By.XPATH, self.profile_path)))
            sleep(0.3)
            element.click()
            sleep(0.3)
            return lvl_image, pfp_image, str(self.driver.current_url)
        except:
            PrintException()

class FaceitLvl:
    def __init__(self, driver, faceit_link):
        self.url = faceit_link
        self.level_path = '#main-container-height-wrapper > div > div.container.main-container.animated.ng-fadeIn.animate-enter-only.flex-1 > section > div > div.col-md-8 > div:nth-child(1) > div > player-game-card > div > div.game-card__info > div.game-card__row.game-card__row--no-spacing > div:nth-child(1) > div > div.stat__icon > skill-icon > svg'
        self.driver = driver
        size = self.driver.get_window_size()
        self.size_x = int(size['width'])
        self.size_y = int(size['height'])
        self.driver.get(self.url)

    def fetch_info(self):
        try:
            element = WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, self.level_path)))
            sleep(0.3)
            lvl_image = io.BytesIO(element.screenshot_as_png)
            return lvl_image
        except:
            PrintException()

def get_faceit_lvl(steam_link):
    driver = get_chromedriver(True)
    driver.set_page_load_timeout(80)
    steamid = SteamID64(driver, steam_link)
    faceit = Faceit(driver, steamid.fetch_info())
    return faceit.fetch_info()

def get_lvl(faceit_link):
    driver = get_chromedriver(True)
    driver.set_page_load_timeout(80)
    faceit = FaceitLvl(driver, faceit_link)
    return faceit.fetch_info()