from flask import Flask, render_template, request
from flask_cors import CORS

from db import mysql_engine
from routes import (
    wine_reviews_search,
    suggest_wines,
    suggest_varietals,
    suggest_regions,
)

# Path to init.sql file. This file can be replaced with your own file for testing on localhost, but do NOT move the init.sql file
mysql_engine.load_file_into_db()

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return render_template('base.html', title="sample html")

@app.route("/wine_reviews")
def wine_reviews():
    return wine_reviews_search(request)

@app.route("/suggest_wines")
def suggest_wine():
    return suggest_wines(request)

@app.route('/suggest_varietals')
def suggest_varietal():
    return suggest_varietals(request)

@app.route('/suggest_regions')
def suggest_region():
    return suggest_regions(request)

app.run(debug=True)
