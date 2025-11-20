import sqlite3
import logging
import sys
from progress.bar import IncrementalBar

logging.basicConfig(encoding="utf-8", level=logging.DEBUG, 
                    format="%(levelname)s %(asctime)s %(message)s",
                    handlers=[logging.FileHandler("log.txt", "w+"), logging.StreamHandler(sys.stdout)])

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect("dbase.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    with open("sq_db.sql", "r") as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()


class DBase:
    def __init__(self, conn: sqlite3.Connection):
        self.__db = conn
        self.__cur = self.__db.cursor()
        self.__log = logging.getLogger(__name__)

    def __del__(self):
        self.__cur = None
        self.__db.close()

    def addCompany(self, fullName, shortName, TID, accreditationDate, leaderTID, leaderName, mainActivity, earnings, expenses, taxPayed, workerCountMean, isActive=True, vacansyCount=None, taxMode=None, taxDebt=None, name=None) -> bool:
        sql = """INSERT INTO company (fullName, shortName, TID, accreditationDate, leaderTID, leaderName, mainActivity, earnings, expenses, taxPayed, workerCountMean, isActive, vacansyCount, taxMod, taxDebt, name) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

        try:
            self.__cur.execute(sql, (fullName, shortName, TID, accreditationDate, leaderTID, leaderName, mainActivity, earnings, expenses, taxPayed, workerCountMean, int(bool(isActive)), vacansyCount, name))
            self.__db.commit()
            return True
        except sqlite3.Error as e:
            self.__log.error("Failed to add company: " + str(e))
        return False

    def getCompanyByID(self, id):
        sql = f"""SELECT * FROM company WHERE id = '{id}'"""
        try:
            self.__cur.execute(sql)
            res = self.__cur.fetchone()
            if res: return res
        except sqlite3.Error as e:
            self.__log.error("Failed to get company by ID: " + str(e))
        return None

    def getCompanyByTID(self, tid):
        sql = f"""SELECT * FROM company WHERE TID = '{tid}'"""
        try:
            self.__cur.execute(sql)
            res = self.__cur.fetchone()
            if res: return res
        except sqlite3.Error as e:
            self.__log.error("Failed to get company by TID: " + str(e))
        return None

    def deleteCompanyByID(self, id) -> bool:
        sql = f"""DELETE FROM company WHERE id = '{id}'"""
        try:
            self.__cur.execute(sql)
            self.__db.commit()
            return True
        except sqlite3.Error as e:
            self.__log.error("Failed to delete company by ID: " + str(e))
        return False
