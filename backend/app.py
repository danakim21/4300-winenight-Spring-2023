import json
import os
from flask import Flask, render_template, request
from flask_cors import CORS
from db import mysql_engine, MYSQL_DATABASE
from helpers.FlavorKeywordsExtractor import FlavorKeywords
from helpers.FlavorTypoCorrector import FlavorTypoCorrector

# Path to init.sql file. This file can be replaced with your own file for testing on localhost, but do NOT move the init.sql file
mysql_engine.load_file_into_db()

app = Flask(__name__)
CORS(app)

def sql_search(wine_name):
    query_sql = f"""SELECT * FROM {MYSQL_DATABASE}.wine_data WHERE LOWER(wine) LIKE '%%{wine_name}%%' LIMIT 10"""
    keys = ["wine", "country", "winery", "category", "designation", "varietal", "appellation", "alcohol", "price", "rating", "reviewer", "review", "price_numeric", "price_range", "alcohol_numeric"]
    data = mysql_engine.query_selector(query_sql)
    return json.dumps([dict(zip(keys, i)) for i in data])

@app.route("/")
def home():
    return render_template('base.html', title="sample html")

@app.route("/wine_data")
def wine_search():
    wine_name = request.args.get("wine")
    return sql_search(wine_name)

# keyword_extractor = FlavorKeywords()
# words = keyword_extractor.flavor_words
# print(words)

flavor_typo_corrector = FlavorTypoCorrector(3) 
original_list = ["friuty", "brightt", "good", "swet", "raspberry", "woodiy", "coke", "dri", "spice", "newflavor"]
new_list = flavor_typo_corrector.get_replaced_flavor_list(original_list)
print(original_list)
print(new_list)

app.run(debug=True)
