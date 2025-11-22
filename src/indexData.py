import logging
import sys
import os
import time
import json
import random
import requests
import zipfile

from progress.bar import IncrementalBar
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support import expected_conditions as EC

DEBUG = False
load_dotenv()
CACHE_FOLDER = os.getenv("CACHE_FOLDER", "cache/")

logging.basicConfig(encoding="utf-8", level=logging.DEBUG if DEBUG else logging.INFO, 
                    format="%(levelname)s %(asctime)s %(message)s",
                    handlers=[logging.FileHandler("log.txt", ("w" if DEBUG else "w+")), logging.StreamHandler(sys.stdout)])

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

def indexWorkerCount(ignoreCache=False) -> list:
    """Returns array[countByFullName, countByTID]"""
    cache = os.path.join(CACHE_FOLDER, "workerCount.json")
    if os.path.exists(cache) and not ignoreCache:
        logging.info("Getting indexed files from cache")
        with open(cache, "r") as f:
            data = json.loads(f.read())
            return data
    else:
        if not os.path.exists("res/workerCount/"):
            logging.info("Getting worker count XML data")
            os.mkdir("res/")
            os.mkdir("res/workerCount")
            tmpFile = "tmp.zip"
            url = "https://file.nalog.ru/opendata/7707329152-sshr2019/data-20251025-structure-20200408.zip"
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(tmpFile, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            logging.info("Extracting archive")
            with zipfile.ZipFile(tmpFile, 'r') as z:
                z.extractall("res/workerCount/")
            os.remove(tmpFile)
        logging.info("Indexing files")
        start = time.time()
        files = os.listdir("res/workerCount")
        bar = IncrementalBar("Indexing worker mean count", max=len(files))
        data = [{}, {}]
        for file in files:
            with open(os.path.join("res/workerCount", file), "r") as f:
                dat = f.read()
            soup = BeautifulSoup(dat, features="xml")
            docs = soup.find_all("Документ")
            for d in docs:
                comp = d.find("СведНП")
                name = str(comp.get_attribute_list("НаимОрг")[0]).strip()
                tid = str(comp.get_attribute_list("ИННЮЛ")[0]).strip()
                count = str(d.find("СведССЧР").get_attribute_list("КолРаб")[0]).strip()
                #data.append({"fullName": name, "TID": tid, "workerCount": count})
                data[0][name] = count
                data[1][tid] = count
            bar.next()
        bar.finish()
        print(f"File processing finished! Process took {time.time() - start:.2f}s")
        logging.debug("Writing cache")
        with open(cache, "w") as f:
            f.write(json.dumps(data))
            return data
    
def getCompaniesPageCountHH():
    logging.info("Getting companies pages count from hh.ru")

    driver = getDriver()
    driver.get("https://kaliningrad.hh.ru/employers_company/informacionnye_tekhnologii_sistemnaya_integraciya_internet")
    
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#HH-React-Root > div > div.HH-MainContent.HH-Supernova-MainContent > div.main-content.main-content_broad-spacing > div > div > div:nth-child(2) > div.pager")))

    html = driver.find_element(By.TAG_NAME, "html").get_attribute("innerHTML")

    # DEBUG
    #with open("hh.html", "r") as f:
    #    html = f.read()

    soup = BeautifulSoup(html, "lxml")
    return len(soup.find("div", class_="pager").find_all("span", recursive=False))

def getCompaniesPage(page=1):
    logging.info(f"Getting companies page {page} from hh.ru")

    url = f"https://kaliningrad.hh.ru/employers_company/informacionnye_tekhnologii_sistemnaya_integraciya_internet?page={page}"

    driver = getDriver()
    driver.get(url)
    
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.employer--u3kJFXzDlcEGXYWV:nth-child(1)")))

    html = driver.find_element(By.TAG_NAME, "html").get_attribute("innerHTML")

    # DEBUG
    #with open("hh.html", "r") as f:
    #    html = f.read()
    
    res = {}

    soup = BeautifulSoup(html, "lxml")
    els = soup.find_all("div", class_="employer--u3kJFXzDlcEGXYWV")
    for el in els:
        name = str(el.find("a").text).strip()
        cnt = str(el.find("div").text).strip()
        res[name] = cnt
    return res

def indexVacancies(ignoreCache=False) -> dict:
    cache = os.path.join(CACHE_FOLDER, "vacansyCount.json")
    if os.path.exists(cache) and not ignoreCache:
        logging.info("Getting hh.ru vacancy data from cache")
        with open(cache, "r") as f:
            data = json.loads(f.read())
            return data
    else:
        logging.info("Indexing vacancy data from hh.ru")
        data = {}
        cnt = int(getCompaniesPageCountHH())
        for page in range(cnt):
            d = getCompaniesPage(page)
            data.update(d)
        logging.info("Writing hh.ru vacancy data in cache")
        with open(cache, "w") as f:
            f.write(json.dumps(data))
            return data

if __name__ == "__main__":
    indexWorkerCount(ignoreCache=True)
    indexVacancies(ignoreCache=True)
