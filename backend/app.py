import json
from flask import Flask, render_template, request
from flask_cors import CORS
from db import mysql_engine, MYSQL_DATABASE

from helpers.SimilarWines import SimilarWines
from helpers.FlavorTypoCorrector import FlavorTypoCorrector
from helpers.booleanSearch import boolean_search
from helpers.moodFilter import mood_filter

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
    # Get user input 
    flavors = request.args.getlist("flavors")
    min_price = request.args.get("minPrice")
    max_price = request.args.get("maxPrice")
    category = request.args.get("category")
    country = request.args.get("country")
    appellation = request.args.get("appellation")
    mood = request.args.getlist("mood")
    wine_param = request.args.get('wine')
    wine_names = [w.strip() for w in wine_param.split(',')] if wine_param else None

    # Query 
    query_sql = f"""
        SELECT * FROM {MYSQL_DATABASE}.wine_data 
        WHERE 1=1
        """
    
    if min_price is not None:
        query_sql += f" AND price_numeric >= {min_price}"

    if max_price is not None:
        query_sql += f" AND price_numeric <= {max_price}"

    if category:
        query_sql += f" AND LOWER(category) = LOWER('{category}')"

    if country:
        query_sql += f" AND LOWER(country) = LOWER('{country}')"

    if appellation:
        query_sql += f" AND LOWER(SUBSTRING_INDEX(appellation, ',', 1)) = LOWER('{appellation}')"
        
    if wine_names:
        wine_list = ", ".join([f'"{w.lower()}"' for w in wine_names])
        query_sql += f" AND (LOWER(wine) IN ({wine_list}) OR LENGTH(TRIM(wine)) = 0)"

    keys = ["wine", "country", "winery", "category", "designation", "varietal", "appellation", "alcohol", "price", "rating", "reviewer", "review", "price_numeric", "price_range", "alcohol_numeric"]
    data = mysql_engine.query_selector(query_sql)

    # Correct typos using minimum edit distance 
    flavor_typo_corrector = FlavorTypoCorrector(3)
    flavors = flavor_typo_corrector.get_replaced_flavor_list(flavors)

    # Get results using boolean search 
    results = boolean_search(data, keys, flavors)

    # Filter results by mood
    if mood:
        results = mood_filter(results, mood)
    
    results = results[:10]

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

@app.route("/similar_wines")
def similar_wine_search():
    wine_name = request.args.get("wine_name")
    sw = SimilarWines(wine_name)
    results = []
    for score, msg_id in sw.search_results[1:11]:
        wine_name = sw.get_wine_name_from_id(msg_id)
        wine_metadata = sw.get_wine_metadata(wine_name)
        price = wine_metadata["price"]
        category = wine_metadata["category"]
        varietal = wine_metadata["varietal"]
        appellation = wine_metadata["appellation"]
        country = wine_metadata["country"]
        results.append({
        "score": score,
        "wine_name": wine_name,
        "price": price,
        "category": category,
        "varietal": varietal,
        "appellation": appellation,
        "country": country
        })

    return json.dumps(results)



app.run(debug=True)
