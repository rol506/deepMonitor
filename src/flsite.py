from flask import Flask, render_template, g, request, url_for, redirect, abort, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from numpy import require
from dbase import DBase, get_db
from parsing import checkTID, update

import pandas as pd
import os
import logging
import datetime
import json

load_dotenv()

app = Flask(__name__)
app.config["DEBUG"] = bool(os.getenv("DEBUG", "False"))
app.config["PORT"] = int(os.getenv("WEB_INTERFACE_PORT", "4221"))
app.template_folder = "../templates/"
app.static_folder = "../static/"
CORS(app, resources={r'/search/*': {"origins": "*"}})

def exportExcel(filename, lst=None):
    db = DBase(get_db())
    records = db.getAllCompanies()

    res = {}

    for r in records:
        keys = list(r.keys())
        values = list(r.values())
        
        for k, v in zip(keys, values):
            if res.get(k) is None:
                res[k] = list()

            if k == "isActive" or k == "isAccredicted":
                if str(v) == "1":
                    res[k].append("Да")
                else:
                    res[k].append("Нет")
            elif v is None:
                res[k].append("Нет данных")
            else:
                res[k].append(v)

    res["ID"] = res.pop("id")
    res["Имя"] = res.pop("name")
    res["Полное наименование"] = res.pop("fullName")
    res["Сокращенное наименование"] = res.pop("shortName")
    res["ИНН"] = res.pop("TID")
    res["ОГРН"] = res.pop("OGRN")
    res["ОКВЭД"] = res.pop("mainActivity")
    res["Дата постановки на учёт"] = res.pop("accreditationDate")
    res["Дата регистрации"] = res.pop("registrationDate")
    res["Действителен"] = res.pop("isActive")
    res["Аккредитация подтверждена"] = res.pop("isAccredicted")
    res["Юридический адрес"] = res.pop("address")

    res.pop("companyTID")
    res["Выручка, руб"] = res.pop("earnings")
    res["Расходы, руб"] = res.pop("expenses")
    res["Сумма уплаченных налогов, руб"] = res.pop("taxPayed")
    res["Среднеписочное число сотрудников"] = res.pop("workerCountMean")
    res["Специальный налоговый режим"] = res.pop("taxMode")
    res["Налоговая задолженность"] = res.pop("taxDebt")
    res["Количество вакансий (hh.ru)"] = res.pop("vacancyCount")

    res["Руководитель"] = res.pop("leaderName")
    res["ИНН руководителя"] = res.pop("leaderTID")
    res["Контактный email"] = res.pop("leaderEmail")
    res["Контактный телефон"] = res.pop("leaderPhone")
    res["Веб-сайт"] = res.pop("leaderWebsite")

    df = pd.DataFrame(res)
    if lst is not None:
        df = df[df["ID"].isin(lst)]
    df.to_excel(filename)

@app.route("/check/<tid>", methods=["POST", "GET"])
def check(tid):
    res = checkTID(tid)
    return jsonify({"result": res})

@app.route("/update", methods=["POST"])
def updateDB():
    return jsonify({"success": True})

@app.route("/add/", methods=["POST"])
def addRecord():
    name = request.form.get("name")
    tid = request.form.get("tid")
    if name is None or tid is None:
        abort(400)
    else:
        success = True
        db = DBase(get_db())
        db.addUpdateRecord(tid, name)
        if request.form.get("update") is not None:
            success = update()
    return redirect(url_for("index"))

@app.route("/table/<page>")
def table(page):
    db = DBase(get_db())
    recs = db.getAllCompanies()
    return jsonify({"dataLength": len(recs), "pageSize": 10, "data": recs})

@app.route("/")
@app.route("/home")
@app.route("/index", methods=["POST", "GET"])
def index():
    dbase = DBase(get_db())
    stats = dbase.getStats()
    return render_template("index.html", stats=stats)

@app.route("/download")
def down():
    exportExcel("export.xlsx")
    return send_file("../export.xlsx")

@app.route("/downloadTable", methods=["POST", "GET"])
def downloadTable():
    exportExcel("export.xlsx", map(int, list(dict(request.form).keys())))
    return send_file("../export.xlsx")

@app.route("/dashboard/<tid>")
def dashboard(tid):
    db = get_db()
    dbase = DBase(db)
    comp = dbase.getCompanyByTID(tid)
    if comp is None:
        logging.warning("Cannot find the " + str(tid))
        return abort(404)
    comp = dict(comp)
    comp["isActive"] = bool(comp["isActive"])
    comp["isAccredicted"] = bool(comp["isAccredicted"])
    comp["vacancyCount"] = 0 if comp.get("vacancyCount") is None else comp["vacancyCount"]
    comp["workerCountMean"] = 0 if comp.get("workerCountMean") is None else comp["workerCountMean"]
    comp["taxMode"] = "Нет данных" if comp.get("taxMode") is None else comp["taxMode"]
    comp["taxDebt"] = 0 if comp.get("taxDebt") is None else comp["taxDebt"]
    comp["OGRN"] = "Нет данных" if comp.get("OGRN") is None else comp["OGRN"]
    if comp["taxPayed"] is None or comp["earnings"] is None or comp["expenses"] is None:
        comp["taxBurden"] = "Нет данных"
    else:
        comp["taxBurden"] = round(int(comp["taxPayed"]) / (int(comp["earnings"]) + int(comp["expenses"])) * 100, 2);
    comp["leaderEmail"] = "Нет данных" if comp.get("leaderEmail") is None else comp["leaderEmail"]
    comp["leaderPhone"] = "Нет данных" if comp.get("leaderPhone") is None else comp["leaderPhone"]
    comp["leaderName"] = "Нет данных" if comp.get("leaderName") is None else comp["leaderName"]
    comp["leaderTID"] = "Нет данных" if comp.get("leaderTID") is None else comp["leaderTID"]
    if comp["earnings"] is None:
        comp["earnings"] = "Нет данных"
    if comp["expenses"] is None:
        comp["expenses"] = "Нет данных"
    if comp["taxPayed"] is None:
        comp["taxPayed"] = "Нет данных"
    if comp["accreditationDate"] is None:
        comp["accreditationDate"] = "Нет данных"
    else:
        comp["accreditationDate"] = datetime.datetime.strptime(comp["accreditationDate"], "%Y-%m-%d").strftime("%Y.%m.%d")
    if comp["registrationDate"] is None:
        comp["registrationDate"] = "Нет данных"
    else:
        comp["registrationDate"] = datetime.datetime.strptime(comp["registrationDate"], "%Y-%m-%d").strftime("%Y.%m.%d")
    lastUpdate = "21.11.2025"
    dbase = DBase(get_db())
    stats = dbase.getStats()
    
    return render_template("dashboard.html", comp=comp, lastUpdate=lastUpdate, stats=stats)

@app.route("/search/<query>")
def search(query):
    db = DBase(get_db())
    res = db.search(query)
    print(res)
    return jsonify(res)

@app.errorhandler(404)
def error404(err):
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=app.config["PORT"])
    #exportExcel("export.xlsx")
