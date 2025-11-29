from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium_stealth import stealth
import selenium
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
import time
import re

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
    field.send_keys(tid)
    field.send_keys(Keys.ENTER)

    logging.info("Waiting for responce")
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#print-page > app-accredited-company > div > div.container.mb-64.search-form > div.grid-row.mb-64 > div.col-3.col-lg-8.col-md-6.push-lg-1 > div > div.mt-24.text-center.ng-star-inserted > a")))
 
    alt = driver.find_element(By.CSS_SELECTOR, ".img-ok").get_attribute("alt")

    driver.close()

    if alt == "OK":
        logging.info(tid + " is accredicted")
        return True
    elif alt == "CROSS":
        logging.info(tid + " is not accredicted")
        return False
    return None

def getTaxData(tid):
    logging.info("Getting tax-related data for " + str(tid))

    driver = getDriver()
    url = f"https://pb.nalog.ru/search.html#mode=search-all&queryAll={tid}"
    driver.get(url)

    wait = WebDriverWait(driver, 5)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.pb-card--clickable")))

    click = driver.find_element(By.CSS_SELECTOR, "div.pb-card--clickable")
    click.click()

    wait = WebDriverWait(driver, 5)
    wait.until(EC.url_changes(url))
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#pnlCompanyMainInfo > div:nth-child(1)")))

    panel = driver.find_element(By.TAG_NAME, "html")
    driver.implicitly_wait(3000)
    html = panel.get_attribute("innerHTML")

    driver.close()

    # DEBUG
    #with open("details.html", "r") as f:
    #    html = f.read()

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
    ogrn = copy.deepcopy(el)

    el = str(soup.find("a", attrs={"data-appeal-kind": "EGRUL_INN"}).find(string=True)).strip()
    tid = copy.deepcopy(el)

    el = str(soup.find("a", attrs={"data-appeal-kind": "ISPRZD"}).text).strip()
    debt = copy.deepcopy(el)

    el = str(soup.find("a", attrs={"data-appeal-kind": "EGRUL_OKVED"}).text).strip()
    mainActivity = copy.deepcopy(el)

    el = str(soup.find("a", attrs={"data-appeal-kind": "EGRUL_ADRES"}).text).strip()
    address = copy.deepcopy(el)

    el = soup.find("a", attrs={"data-appeal-kind": "TAXMODE"})
    if el is None:
        taxMode = None
    else:
        taxMode = copy.deepcopy(str(el.text).strip())

    el = soup.find("span", class_="pb-otch-status")
    if el is None:
        taxDebt = None
    else:
        taxDebt = copy.deepcopy(str(el.text).strip())

    el = soup.select("div.ml-5 > a:nth-child(2)")
    if el != []:
        earnings = str(copy.deepcopy(el[0]).text[:-1]).strip().replace(" ", "")
    else:
        earnings = None

    el = soup.select("div.ml-5 > a:nth-child(2)")
    if el != []:
        expenses = str(copy.deepcopy(el[0]).text[:-1]).strip().replace(" ", "")
    else:
        expenses = None

    el = soup.find("a", attrs={"data-appeal-kind": "TAXPAY"})
    if el is None:
        taxPay = None
    else:
        taxPay = copy.deepcopy(str(el.text)[:-1].strip()).replace(" ", "")

    regDate = soup.select("#pnlCompanyLeftCol > div:nth-child(5) > div:nth-child(1) > div:nth-child(2)")
    if regDate != []:
        regDate = datetime.strptime(str(regDate[0].text).strip(), "%d.%m.%Y").strftime("%Y-%m-%d")
    else:
        regDate = None

    accrDate = soup.select("div.pb-company-multicolumn-item:nth-child(11) > div:nth-child(1) > div:nth-child(2)")
    if accrDate != []:
        accrDate = datetime.strptime(str(accrDate[0].text).strip(), "%d.%m.%Y").strftime("%Y-%m-%d")
    else:
        accrDate = None

    el = soup.select("#rupr > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > span:nth-child(1)")
    if el != []:
        leaderName = copy.deepcopy(str(el[0].text)[:-1].strip())
    else:
        leaderName = None

    el = soup.select("#rupr > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2)")
    if el != []:
        leaderTID = copy.deepcopy(str(el[0].text)[:-1].strip())
    else:
        leaderTID = None

    if debt == "Не имеет задолженность":
        debt = "0"

    res = {
            "fullName": fullName,
            "shortName": shortName,
            "TID": tid,
            "ogrn": ogrn,
            "isActive": isActive,
            "debt": debt,
            "mainActivity": mainActivity,
            "registrationDate": regDate,
            "accreditationDate": accrDate,
            "taxPayed": taxPay,
            "earnings": earnings,
            "expenses": expenses,
            "leaderName": leaderName,
            "leaderTID": leaderTID,
            "address": address,
            "taxMode": taxMode,
            "taxDebt": taxDebt,
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

def updateData(tid, name) -> bool:
    logging.info("Updating data for " + str(tid))
    try:
        workerCounts = indexWorkerCount()[1]
        vacancies = indexVacancies()
        res = getTaxData(tid)

        res["workerCountMean"] = workerCounts.get(tid)
        res["vanacyCount"] = vacancies.get(name)
        res["isAccredicted"] = checkAccredited(tid)

        db = DBase(get_db())
        if not db.removeCompanyByTID(tid):
            logging.error("Failed to delete old record!")
            return False
        if not db.addCompany(res["fullName"], res["shortName"], tid, res["ogrn"], res["isActive"], res["isAccredicted"], res["leaderName"], res["leaderTID"], 
                             name, res["mainActivity"], res["accreditationDate"],
                             res["registrationDate"], res["address"], res["earnings"], res["expenses"], res["taxPayed"], res["workerCountMean"],
                             res["taxMode"], res["taxDebt"], res["vanacyCount"]):
            logging.error("Failed to add updated record!")
            return False
        return True
    except selenium.common.exceptions.ElementClickInterceptedException:
        logging.warning("A click was intercepted! Restarting recursivly")
        return updateData(tid, name)
    except:
        logging.error(tid + " failed! (Maybe it is not a company?)")
        return False

def parseListPage(url, page):
    logging.info("Parsing company list")

    #driver = getDriver()
    #driver.get(url + "?page=" + str(page))

    #wait = WebDriverWait(driver, 20)
    #wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.tr")))

    #panel = driver.find_element(By.TAG_NAME, "html")
    #html = panel.get_attribute("innerHTML")

    #driver.close()

    # DEBUG
    with open("list.html", "r") as f:
        html = f.read()

    res = []
    soup = BeautifulSoup(html, "lxml")

    def inner():
        for p in pairs:
            k = p.find("div", class_="td__caption")
            v = p.find("div", class_="td__text")
            if k is None:
                a = p.find("a", recursive=False)
                if str(a.text).startswith("ИП"):
                    return
                continue
            if str(k.text).strip() == "ИНН:":
                res.append(str(v.text).strip())

    els = soup.find_all("div", class_="tr")
    for el in els:
        pairs = el.find_all("div", class_="td")
        inner()

    return res

def checkTID(tid) -> bool:
    logging.info("checking " + str(tid))

    html = requests.post("https://bik-info.ru/inn.html", data={"inn": tid, "inn_test": "1"}).text
    soup = BeautifulSoup(html, "lxml")
    if str(soup.find("strong").text).strip() == "Верно!":
        return True
    else:
        return False

def findTID(url):
    logging.info("looking for TID in " + url)

    driver = getDriver()
    driver.get(url)

    driver.implicitly_wait(1)

    panel = driver.find_element(By.TAG_NAME, "html")
    html = panel.get_attribute("innerHTML")

    matches = list(filter(checkTID, re.findall(r"[012345679]\d\d\d\d\d\d\d\d\d", html)))
    driver.close()
    return matches

def update():
    # UPDATE DATA FROM LOOKUP
    logging.info("Updating database")
    db = DBase(get_db())
    recs = db.getLookupRecords()
    for r in recs:
        if not updateData(r["TID"], r["name"]):
            logging.error("Failed to update database")
            return False
    logging.info("Database upgraded successfully")
    return True

if __name__ == "__main__":
    update()

    #print(getTaxData("3906900574"))
    #print(getCompaniesPageCountHH())
    #print(loadFromExcel("data.xlsx"))

    #ids = ["7718620740","7816263857","9710138465","3900023944","9710140792","9710140721","9710113887","7806174380","9710089440","9710090492"]
    #updateData("3906900574", "KODE")
    #for i in ids:
    #    updateData(i, "")

    #url = "https://www.1cont.ru/contragent/by-okved/razrabotka-kompjhyuternogo-programmnogo-obespecheniya-konsuljhtacionnye-uslugi-v-dannoy-oblasti-i-drugie-soputstvuyushhie-uslugi_62"
    #url = "https://www.1cont.ru/contragent/by-okved/deyateljhnostjh-v-sfere-telekommunikaciy_61"
    #lst = []
    #for i in range(11):
    #    lst += parseListPage(url, i+1)
    #    time.sleep(0.5)
    #print(lst)
    ##random.shuffle(lst)
    #for i, l in enumerate(lst):
    #    if i > 10:
    #        break
    #    #updateData(l, "")

    #matches = findTID("https://kaliningrad.hh.ru/employers_company/informacionnye_tekhnologii_sistemnaya_integraciya_internet?page=0")
    #print(matches)
