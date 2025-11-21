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

    #def addCompany(self, fullName, shortName, TID, accreditationDate, leaderTID, leaderName, mainActivity, earnings, expenses, taxPayed, workerCountMean, isActive=True, vacansyCount=None, taxMode=None, taxDebt=None, name=None) -> bool:
    #    sql = """INSERT INTO company (fullName, shortName, TID, accreditationDate, leaderTID, leaderName, mainActivity, earnings, expenses, taxPayed, workerCountMean, isActive, vacancyCount, taxMod, taxDebt, name) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

    #    try:
    #        self.__cur.execute(sql, (fullName, shortName, TID, accreditationDate, leaderTID, leaderName, mainActivity, earnings, expenses, taxPayed, workerCountMean, int(bool(isActive)), vacansyCount, name))
    #        self.__db.commit()
    #        return True
    #    except sqlite3.Error as e:
    #        self.__log.error("Failed to add company: " + str(e))
    #    return False

    def addCompany(self, fullName, shortName, tid, ogrn, isActive, leaderName, leaderTID,
                   name=None, mainActivity=None,
                   accreditationDate=None, registrationDate=None, address=None, earnings=None, expenses=None,
                   taxPayed=None, workerCountMean=None, taxMode=None,
                   taxDebt=None, vacancyCount=None,
                   leaderEmail=None, leaderPhone=None) -> bool:
        try:
            sql = """INSERT INTO general (name, fullName, shortName, TID, OGRN, mainActivity, accreditationDate, registrationDate, isActive, address) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            self.__cur.execute(sql,(name, fullName, shortName, tid, ogrn,
                                   mainActivity, accreditationDate, registrationDate, int(isActive), address))
            sql="""INSERT INTO finance (companyTID, earnings, expenses, taxPayed, workerCountMean, taxMode, taxDebt, vacancyCount) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
            self.__cur.execute(sql,(tid, earnings, expenses, taxPayed, workerCountMean, taxMode, taxDebt, vacancyCount))
            sql = """INSERT INTO leader (companyTID, name, TID, email, phone) VALUES (?, ?, ?, ?, ?)"""
            self.__cur.execute(sql, (tid, leaderName, leaderTID, leaderEmail, leaderPhone))
            self.__db.commit()
            return True
        except sqlite3.Error as e:
            self.__log.error("Failed to add company: " + str(e))
        return False

    def getCompanyByTID(self, tid):
        sql = f"""SELECT * FROM general INNER JOIN finance ON general.TID = finance.companyTID LEFT JOIN leader ON general.TID = leader.companyTID"""
        try:
            self.__cur.execute(sql)
            res = self.__cur.fetchone()
            if res: return res
        except sqlite3.Error as e:
            self.__log.error("Failed to get company data by TID: " + str(e))
        return None

    def removeCompanyByTID(self, tid) -> bool:
        try:
            sql = f"""DELETE FROM general WHERE TID = {tid}"""
            self.__cur.execute(sql)
            sql = f"""DELETE FROM finance WHERE companyTID = {tid}"""
            self.__cur.execute(sql)
            sql = f"""DELETE FROM leader WHERE companyTID = {tid}"""
            self.__cur.execute(sql)
            self.__db.commit()
            return True
        except sqlite3.Error as e:
            self.__log.error("Failed to delete company data by TID: " + str(e))
        return False

    def updateCompany(self, tid, fullName=None, shortName=None, ogrn=None, isActive=None, leaderName=None,
                      leaderTID=None, name=None, mainActivity=None, accreditationDate=None, registrationDate=None, address=None,
                      earnings=None, expenses=None, taxPayed=None, workerCountMean=None, taxMode=None,
                      taxDebt=None, vacancyCount=None, leaderEmail=None, leaderPhone=None) -> bool:
        data = self.getCompanyByTID(tid)
        if data is None:
            self.__log.error("Failed to update data: cannot fetch initial values")
            return False
        data = dict(data)
        fullName = data["fullName"] if fullName is None else fullName
        shortName = data["shortName"] if shortName is None else shortName
        ogrn = data["OGRN"] if ogrn is None else ogrn
        isActive = data["isActive"] if isActive is None else isActive
        leaderName = data["leaderName"] if leaderName is None else leaderName
        leaderTID = data["leaderTID"] if leaderTID is None else leaderTID
        name = data["name"] if name is None else name
        mainActivity = data["mainActivity"] if mainActivity is None else mainActivity
        accreditationDate = data["accreditationDate"] if accreditationDate is None else accreditationDate
        registrationDate = data["registrationDate"] if registrationDate is None else registrationDate
        address = data["address"] if address is None else address
        earnings = data["earnings"] if earnings is None else earnings
        expenses = data["expenses"] if expenses is None else expenses
        taxPayed = data["taxPayed"] if taxPayed is None else taxPayed
        workerCountMean = data["workerCountMean"] if workerCountMean is None else workerCountMean
        taxMode = data["taxMode"] if taxMode is None else taxMode
        taxDebt = data["taxDebt"] if taxDebt is None else taxDebt
        vacancyCount = data["vacancyCount"] if vacancyCount is None else vacancyCount
        leaderEmail = data["leaderEmail"] if leaderEmail is None else leaderEmail
        leaderPhone = data["leaderPhone"] if leaderPhone is None else leaderPhone

        if not self.removeCompanyByTID(tid):
            self.__log.error("Failed to remove old company record by TID")
            return False
        if not self.addCompany(fullName, shortName, tid, ogrn, isActive, leaderName, leaderTID, name, mainActivity,
                        accreditationDate, registrationDate, address, earnings, expenses, taxPayed, workerCountMean, taxMode,
                               taxDebt, vacancyCount, leaderEmail, leaderPhone):
            self.__log.error("Failed to add new company record!")
            return False

        return True 
