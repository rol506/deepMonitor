from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from indexData import indexVacancies, indexWorkerCount

import requests
import random
import logging
import sys
import copy
import pandas as pd

from dbase import DBase, get_db

DEBUG = False

logging.basicConfig(encoding="utf-8", level=logging.DEBUG if DEBUG else logging.INFO, 
                    format="%(levelname)s %(asctime)s %(message)s",
                    handlers=[logging.FileHandler("log.txt", ("w" if DEBUG else "w+")), logging.StreamHandler(sys.stdout)])

logging.debug("Loading dotenv")
load_dotenv()

def getDriver() -> webdriver.Chrome:
    logging.debug("Creating stealth Chrome driver")
    service = ChromeService(executable_path=ChromeDriverManager().install())
    options = webdriver.ChromeOptions()

    options.add_argument("--headless")
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-extensions')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    #options.add_experimental_option("detach", True) # Browser remains unclosed

    driver = webdriver.Chrome(service=service, options=options)

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
    ]

    user_agent = random.choice(user_agents)

    options.add_argument(f'user-agent={user_agent}')

    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    return driver

def checkAccredited(tid: str):
    logging.info("Checking accreditation")

    driver = getDriver()
    logging.debug("Getting main page")
    driver.get("https://www.gosuslugi.ru/itorgs")
    
    logging.info("Waiting for page to load")
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type=\"text\"]")))

    logging.info("Sending keys")
    field = driver.find_element(By.CSS_SELECTOR, "input[type=\"text\"]") 
    field.send_keys(str(tid))
    field.send_keys(Keys.ENTER)

    logging.info("Waiting for responce")
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#print-page > app-accredited-company > div > div.container.mb-64.search-form > div.grid-row.mb-64 > div.col-3.col-lg-8.col-md-6.push-lg-1 > div > div.mt-24.text-center.ng-star-inserted > a")))
 
    alt = driver.find_element(By.CSS_SELECTOR, ".img-ok").get_attribute("alt")

    if alt == "OK":
        return True
    elif alt == "CROSS":
        return False
    return None

def getTaxData(tid):
    logging.info("Getting tax-related data")

    #driver = getDriver()
    #url = f"https://pb.nalog.ru/search.html#mode=search-all&queryAll={tid}"
    #driver.get(url)

    #wait = WebDriverWait(driver, 20)
    #wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.pb-card--clickable")))

    #click = driver.find_element(By.CSS_SELECTOR, "div.pb-card--clickable")
    #click.click()

    #wait = WebDriverWait(driver, 20)
    #wait.until(EC.url_changes(url))
    #wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.pb-company-name")))

    #panel = driver.find_element(By.CSS_SELECTOR, "#pnlCompany")
    #html = panel.get_attribute("innerHTML")
    #print("HTML: " + html)
    #driver.implicitly_wait(3000)
    #html = panel.get_attribute("innerHTML")
    #print("HTML: " + html)

    # DEBUG
    with open("details.html", "r") as f:
        html = f.read()

    soup = BeautifulSoup(html, "lxml")

    # fullName, shortName, registration, tid, isActive, debt, workerCountMean
    el = str(soup.find("span", class_="pb-subject-status").find(string=True)).strip()
    if el == "Действующая организация":
        isActive = True
    else:
        isActive = False

    el = str(soup.find("a", attrs={"data-appeal-kind": "EGRUL_FULLNAME"}).find(string=True)).strip()
    fullName = copy.deepcopy(el)

    el = str(soup.find("a", attrs={"data-appeal-kind": "EGRUL_SHORTNAME"}).find(string=True)).strip()
    shortName = copy.deepcopy(el)

    el = str(soup.find("a", attrs={"data-appeal-kind": "EGRUL_OGRN"}).find(string=True)).strip()
    registration = copy.deepcopy(el)

    el = str(soup.find("a", attrs={"data-appeal-kind": "EGRUL_INN"}).find(string=True)).strip()
    tid = copy.deepcopy(el)

    el = str(soup.find("a", attrs={"data-appeal-kind": "ISPRZD"}).text).strip()
    debt = copy.deepcopy(el)
    if debt == "Не имеет задолженность":
        debt = "0"

    res = {
            "fullName": fullName,
            "shortName": shortName,
            "TID": tid,
            "registration": registration,
            "isActive": isActive,
            "debt": debt,
            }
    return res

def loadFromExcel(filename):
    df = pd.read_excel(filename)
    db = get_db()
    dbase = DBase(db)

    #vacansies = indexVacancies()

    for idx, d in df.iterrows():
        date = d["Дата включения в реестр МСП"]
        if type(date) == datetime:
            date = date.strftime("%Y-%m-%d")
        else:
            date = None

        leader = d["ИНН, ФИО руководителя"].split(",")

        dbase.addCompany(
                fullName=d["Полное наименование"],
                shortName=d["Сокращенное наименование"],
                TID=d["ИНН"],
                accreditationDate=date,
                leaderTID=leader[0].strip(),
                leaderName=leader[1].strip(),
                mainActivity=d["Основной ОКВЭД"],
                earnings=d["Выручка, руб."],
                expenses=d["Расходы, руб."],
                taxPayed=d["Сумма уплаченных налогов, руб."],
                workerCountMean=d["Среднесписочная численность"],
                )

if __name__ == "__main__":
    ids = [
            "7718620740",
            "7816263857",
            "9710138465",
            "3900023944",
            "9710140792",
            "9710140721",
            "9710113887",
            "7806174380",
            "9710089440",
            "9710090492",
            ]
    #print(getTaxData("7718620740"))
    #print(getCompaniesPageCountHH())
    print(loadFromExcel("data.xlsx"))
