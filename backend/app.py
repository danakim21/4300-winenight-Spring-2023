import json
import os
from flask import Flask, render_template, request
from flask_cors import CORS
from db import mysql_engine, MYSQL_DATABASE
from helpers.FlavorKeywordsExtractor import FlavorKeywords
from helpers.FlavorTypoCorrector import FlavorTypoCorrector
from helpers.booleanSearch import boolean_search

# Path to init.sql file. This file can be replaced with your own file for testing on localhost, but do NOT move the init.sql file
mysql_engine.load_file_into_db()

app = Flask(__name__)
CORS(app)

def sql_search(wine_name):
    query_sql = f"""SELECT * FROM {MYSQL_DATABASE}.wine_data WHERE LOWER(wine) LIKE '%%{wine_name}%%' LIMIT 10"""
    keys = ["wine", "country", "winery", "category", "designation", "varietal", "appellation", "alcohol", "price", "rating", "reviewer", "review", "price_numeric", "price_range", "alcohol_numeric"]
    data = mysql_engine.query_selector(query_sql)
    return json.dumps([dict(zip(keys, i)) for i in data])

def sql_search_reviews():
    user_input = request.args.getlist("keywords")
    query_sql = f"""SELECT * FROM {MYSQL_DATABASE}.wine_data"""
    keys = ["wine", "country", "winery", "category", "designation", "varietal", "appellation", "alcohol", "price", "rating", "reviewer", "review", "price_numeric", "price_range", "alcohol_numeric"]
    data = mysql_engine.query_selector(query_sql)

    flavor_typo_corrector = FlavorTypoCorrector(3)
    user_input = flavor_typo_corrector.get_replaced_flavor_list(user_input)

    results = boolean_search(data, keys, user_input)
    return json.dumps(results)

@app.route("/")
def home():
    return render_template('base.html', title="sample html")

@app.route("/wine_data")
def wine_search():
    wine_name = request.args.get("wine")
    return sql_search(wine_name)

@app.route("/wine_reviews")
def wine_reviews_search():
    return sql_search_reviews()

app.run(debug=True)
