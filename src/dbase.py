import sqlite3
import logging
import sys
from progress.bar import IncrementalBar

logging.basicConfig(encoding="utf-8", level=logging.DEBUG, 
                    format="%(levelname)s %(asctime)s %(message)s",
                    handlers=[logging.FileHandler("log.txt", "w+"), logging.StreamHandler(sys.stdout)])

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect("dbase.db")
    conn.row_factory = dict_factory
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

    def addUpdateRecord(self, tid, name) -> bool:
        try:
            sql = """INSERT INTO lookup (actualName, TID) VALUES (?,?)"""
            self.__cur.execute(sql, (name, tid))
            self.__db.commit()
            return True
        except sqlite3.Error as e:
            self.__log.error("Failed to add record to lookup table: " + str(e))
        return False

    def getLookupRecords(self):
        try:
            sql = """SELECT TID, actualName AS name FROM lookup"""
            self.__cur.execute(sql)
            res = self.__cur.fetchall()
            if res: return res
        except sqlite3.Error as e:
            self.__log.error("Failed to get data from lookup table: " + str(e))
        return None

    def addCompany(self, fullName, shortName, tid, ogrn, isActive, isAccredicted, leaderName=None, leaderTID=None,
                   name=None, mainActivity=None,
                   accreditationDate=None, registrationDate=None, address=None, earnings=None, expenses=None,
                   taxPayed=None, workerCountMean=None, taxMode=None,
                   taxDebt=None, vacancyCount=None,
                   leaderEmail=None, leaderPhone=None, leaderWebsite=None) -> bool:
        try:
            sql = """INSERT INTO general (name, fullName, shortName, TID, OGRN, mainActivity, accreditationDate, registrationDate, isActive, isAccredicted, address) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            self.__cur.execute(sql,(name, fullName, shortName, tid, ogrn,
                                   mainActivity, accreditationDate, registrationDate, int(isActive), int(isAccredicted), address))
            sql="""INSERT INTO finance (companyTID, earnings, expenses, taxPayed, workerCountMean, taxMode, taxDebt, vacancyCount) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
            self.__cur.execute(sql,(tid, earnings, expenses, taxPayed, workerCountMean, taxMode, taxDebt, vacancyCount))
            sql = """INSERT INTO leader (companyTID, name, TID, email, phone, website) VALUES (?, ?, ?, ?, ?, ?)"""
            self.__cur.execute(sql, (tid, leaderName, leaderTID, leaderEmail, leaderPhone, leaderWebsite))
            self.__db.commit()
            return True
        except sqlite3.Error as e:
            self.__log.error("Failed to add company: " + str(e))
        return False

    def getCompanyByTID(self, tid):
        sql = f"""SELECT * FROM general INNER JOIN finance ON general.TID = finance.companyTID LEFT JOIN leader ON general.TID = leader.companyTID WHERE general.TID = '{tid}'"""
        try:
            self.__cur.execute(sql)
            res = self.__cur.fetchone()
            if res: return res
        except sqlite3.Error as e:
            self.__log.error("Failed to get company data by TID: " + str(e))
        return None

    def getAllCompanies(self):
        sql = f"""SELECT leader.TID AS leaderTID, leader.phone AS leaderPhone, leader.email as leaderEmail, leader.name as leaderName, leader.website AS leaderWebsite, general.TID AS TID, finance.*, general.* FROM general INNER JOIN finance ON general.TID = finance.companyTID LEFT JOIN leader ON general.TID = leader.companyTID"""
        try:
            self.__cur.execute(sql)
            res = self.__cur.fetchall()
            if res: return res
        except sqlite3.Error as e:
            self.__log.error("Failed to get all companies: " + str(e))
        return None

    def search(self, query):
        res = []
        try:
            sql = f"""SELECT TID, shortName FROM general WHERE fullName LIKE '%{query}%'"""
            self.__cur.execute(sql)
            r = self.__cur.fetchall()
            if r:
                res += r

            sql = f"""SELECT TID, shortName FROM general WHERE shortName LIKE '%{query}%'"""
            self.__cur.execute(sql)
            r = self.__cur.fetchall()
            if r:
                res += r

            sql = f"""SELECT TID, shortName FROM general WHERE TID LIKE '%{query}%'"""
            self.__cur.execute(sql)
            r = self.__cur.fetchall()
            if r:
                res += r

            sql = f"""SELECT TID, shortName FROM general WHERE OGRN LIKE '%{query}%'"""
            self.__cur.execute(sql)
            r = self.__cur.fetchall()
            if r:
                res += r

            sql = f"""SELECT TID, shortName FROM general WHERE name LIKE '%{query}%'"""
            self.__cur.execute(sql)
            r = self.__cur.fetchall()
            if r:
                res += r
            
            s = []
            for d in res:
                if not d in s:
                    s.append(d)
            return s
        except sqlite3.Error as e:
            self.__log.error("Search failed: " + str(e))
        return None

    def getStats(self):
        """Returns DB statistics [total companies, total workers, total accredicted]"""
        try:
            sql = f"""SELECT COUNT(*) AS totalCompanies FROM general"""
            self.__cur.execute(sql)
            res = self.__cur.fetchone()
            totalCompanies = res["totalCompanies"]
            sql = f"""SELECT SUM(workerCountMean) AS totalWorkers FROM finance"""
            self.__cur.execute(sql)
            res = self.__cur.fetchone()
            totalWorkers = res["totalWorkers"]
            sql = f"""SELECT COUNT(*) AS totalAccredicted FROM general WHERE isAccredicted = '1'"""
            self.__cur.execute(sql)
            res = self.__cur.fetchone()
            totalAccredicted = res["totalAccredicted"]
            return [totalCompanies, totalWorkers, totalAccredicted]
        except sqlite3.Error as e:
            self.__log.error("Failed to get stats from DB: " + str(e))
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

    def updateCompany(self, tid, fullName=None, shortName=None, ogrn=None, isActive=None, isAccredicted=None, leaderName=None,
                      leaderTID=None, name=None, mainActivity=None, accreditationDate=None, registrationDate=None, address=None,
                      earnings=None, expenses=None, taxPayed=None, workerCountMean=None, taxMode=None,
                      taxDebt=None, vacancyCount=None, leaderEmail=None, leaderPhone=None, leaderWebsite=None) -> bool:
        data = self.getCompanyByTID(tid)
        if data is None:
            self.__log.error("Failed to update data: cannot fetch initial values")
            return False
        data = dict(data)
        fullName = data["fullName"] if fullName is None else fullName
        shortName = data["shortName"] if shortName is None else shortName
        ogrn = data["OGRN"] if ogrn is None else ogrn
        isActive = data["isActive"] if isActive is None else isActive
        isAccredicted = data["isAccredicted"] if isAccredicted is None else isAccredicted
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
        leaderWebsite = data["leaderWebsite"] if leaderWebsite is None else leaderWebsite

        if not self.removeCompanyByTID(tid):
            self.__log.error("Failed to remove old company record by TID")
            return False
        if not self.addCompany(fullName, shortName, tid, ogrn, isActive, isAccredicted, leaderName, leaderTID, name, mainActivity,
                        accreditationDate, registrationDate, address, earnings, expenses, taxPayed, workerCountMean, taxMode,
                               taxDebt, vacancyCount, leaderEmail, leaderPhone, leaderWebsite):
            self.__log.error("Failed to add new company record!")
            return False

        return True 
