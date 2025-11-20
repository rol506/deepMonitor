from flask import Flask, render_template, g, request, url_for, redirect, abort
from dotenv import load_dotenv
from dbase import DBase, get_db

import os

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
        return abort(404)
    comp = dict(comp)
    if comp.get("accreditationDate") is not None:
        comp["isAccredicted"] = True
    else:
        comp["isAccredicted"] = False

    comp["isActive"] = bool(comp["isActive"])
    comp["vacansyCount"] = 0 if comp.get("vacansyCount") is None else comp["vacansyCount"]
    comp["workerCountMean"] = 0 if comp.get("workerCountMean") is None else comp["workerCountMean"]
    comp["taxMode"] = "Нет данных" if comp.get("taxMode") is None else comp["taxMode"]
    comp["taxDebt"] = 0 if comp.get("taxDebt") is None else comp["taxDebt"]
    return render_template("dashboard.html", comp=comp)

@app.errorhandler(404)
def error404(err):
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=app.config["PORT"])
