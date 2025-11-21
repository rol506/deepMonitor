from flask import Flask, render_template, g, request, url_for, redirect, abort
from dotenv import load_dotenv
from dbase import DBase, get_db

import os
import logging

load_dotenv()

app = Flask(__name__)
app.config["DEBUG"] = bool(os.getenv("DEBUG", "False"))
app.config["PORT"] = int(os.getenv("WEB_INTERFACE_PORT", "4221"))
app.template_folder = "../templates/"
app.static_folder = "../static/"

@app.route("/")
@app.route("/home")
@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/dashboard/<tid>")
def dashboard(tid):
    db = get_db()
    dbase = DBase(db)
    comp = dbase.getCompanyByTID(tid)
    if comp is None:
        logging.warning("Cannot find the " + str(tid))
        return abort(404)
    comp = dict(comp)
    if comp.get("accreditationDate") is not None:
        comp["isAccredicted"] = True
    else:
        comp["isAccredicted"] = False

    comp["isActive"] = bool(comp["isActive"])
    comp["vacancyCount"] = 0 if comp.get("vacancyCount") is None else comp["vacancyCount"]
    comp["workerCountMean"] = 0 if comp.get("workerCountMean") is None else comp["workerCountMean"]
    comp["taxMode"] = "Нет данных" if comp.get("taxMode") is None else comp["taxMode"]
    comp["taxDebt"] = 0 if comp.get("taxDebt") is None else comp["taxDebt"]
    comp["OGRN"] = "Нет данных" if comp.get("OGRN") is None else comp["OGRN"]
    comp["taxBurden"] = round(int(comp["taxPayed"]) / (int(comp["earnings"]) + int(comp["expenses"])) * 100, 2);
    comp["leaderEmail"] = "Нет данных" if comp.get("leaderEmail") is None else comp["leaderEmail"]
    comp["leaderPhone"] = "Нет данных" if comp.get("leaderPhone") is None else comp["leaderPhone"]
    lastUpdate = "20.11.2025"
    return render_template("dashboard.html", comp=comp, lastUpdate=lastUpdate)

@app.errorhandler(404)
def error404(err):
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=app.config["PORT"])
