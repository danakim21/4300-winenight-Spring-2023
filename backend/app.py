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

def sql_search(wine_name, limit=10):
    query_sql = f"""SELECT * FROM {MYSQL_DATABASE}.wine_data WHERE LOWER(wine) LIKE '%%{wine_name}%%' LIMIT {limit}"""
    keys = ["wine", "country", "winery", "category", "designation", "varietal", "appellation", "alcohol", "price", "rating", "reviewer", "review", "price_numeric", "price_range", "alcohol_numeric"]
    data = mysql_engine.query_selector(query_sql)
    return json.dumps([dict(zip(keys, i)) for i in data])

def sql_search_reviews(similarity_scores=None):
    # Get user input 
    flavors = request.args.getlist("flavors")
    min_price = request.args.get("minPrice")
    max_price = request.args.get("maxPrice")
    category = request.args.get("category")
    country = request.args.get("country")
    varietal = request.args.get("varietal")
    appellation = request.args.get("appellation")
    mood = request.args.getlist("mood")
    wine_param = request.args.get('wine')
    wine_names = [w.strip() for w in wine_param.split(',')] if wine_param else None

    # Query 
    query_sql = f"""
        SELECT * FROM {MYSQL_DATABASE}.wine_data 
        WHERE 1=1
        """
    
    if similarity_scores:
        wine_names_from_similarity_scores = [score['wine_name'].lower().replace("%", "%%") for score in similarity_scores]
        wine_names_list = ', '.join([f'"{wine_name}"' for wine_name in wine_names_from_similarity_scores])
        query_sql += f" AND LOWER(wine) IN ({wine_names_list})"
    
    
    if min_price is not None:
        query_sql += f" AND price_numeric >= {min_price}"

    if max_price is not None:
        query_sql += f" AND price_numeric <= {max_price}"

    if category:
        query_sql += f" AND LOWER(category) = LOWER('{category}')"

    if varietal:
        query_sql += f" AND LOWER(varietal) = LOWER('{varietal}')"

    if country:
        query_sql += f" AND LOWER(country) = LOWER('{country}')"

    if appellation:
        query_sql += f" AND LOWER(SUBSTRING_INDEX(appellation, ',', 1)) = LOWER('{appellation}')"
        
    if wine_names:
        wine_list = ", ".join([f'"{w.lower()}"' for w in wine_names])
        query_sql += f" AND (LOWER(wine) IN ({wine_list}) OR LENGTH(TRIM(wine)) = 0)"

    keys = ["wine", "country", "winery", "category", "designation", "varietal", "appellation", "alcohol", "price", "rating", "reviewer", "review", "price_numeric", "price_range", "alcohol_numeric"]
    query_result = mysql_engine.query_selector(query_sql)
    results = [dict(zip(keys, row)) for row in query_result] 

    if similarity_scores is not None:
        similarity_scores_dict = {score['wine_name'].lower(): score for score in similarity_scores}
        
        for result in results:
            wine_name = result['wine'].lower()
            if wine_name in similarity_scores_dict:
                result.update(similarity_scores_dict[wine_name])
    else:
        results = boolean_search(results, flavors, similarity_scores=None, flavorSearch=True)

    # Filter results by mood
    if mood:
        if similarity_scores is None:
            results = mood_filter(results, mood, flavorSearch=True)
        elif similarity_scores is not None and flavors[0] == '':
            results = mood_filter(results, mood, similar=True)
        else:
            results = mood_filter(results, mood, both=True)
    results = results[:6]
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
    # Get user input 
    wine_name = request.args.get("wine_name")
    flavors = request.args.getlist("flavors")
    # ... (Keep the other user input parameters)

    flavor_typo_corrector = FlavorTypoCorrector(3)
    flavors = flavor_typo_corrector.get_replaced_flavor_list(flavors)

    similarity_scores = None

    # Check if wine_name is provided
    if wine_name != "null":
        sw = SimilarWines(wine_name)
        similarity_scores = sw.get_similarity_scores(limit=3000)

        # If flavors are also provided, filter the similarity_scores by flavors
        if len(flavors) > 0 and flavors[0] != '':
            wine_data = [item for item in similarity_scores]
            keys = ["score", "wine_name", "price", "category", "varietal", "appellation", "country", "review"]
            filtered_wine_data = boolean_search(wine_data, flavors, similarity_scores)
            similarity_scores = [{'wine_name': item['wine_name'], 'combined_score': item['combined_score'], 'score': item['score'], 'term_score': item['term_score']} for item in filtered_wine_data] 

    
    results = sql_search_reviews(similarity_scores)
    return results

@app.route("/similar_wines")
def similar_wine_search():
    wine_name = request.args.get("wine_name")
    limit = request.args.get("limit", default=10000, type=int)
    sw = SimilarWines(wine_name)
    scores_and_details = sw.get_similarity_scores()
    return json.dumps(scores_and_details)

@app.route("/suggest_wines")
def suggest_wines():
    input = request.args.get("input")
    suggestions = fetch_wine_suggestions(input)
    return json.dumps(suggestions)

def fetch_wine_suggestions(input):
    query = f"SELECT wine FROM {MYSQL_DATABASE}.wine_data WHERE LOWER(wine) LIKE '%%{input}%%' LIMIT 6"
    data = mysql_engine.query_selector(query)
    wine_names = [row[0] for row in data]
    return wine_names

@app.route('/suggest_varietals')
def suggest_varietals():
    input = request.args.get('input')
    suggestions = fetch_varietal_suggestions(input)
    return json.dumps(suggestions)

def fetch_varietal_suggestions(varietal_name):
    query_sql = f"""SELECT DISTINCT varietal FROM {MYSQL_DATABASE}.wine_data WHERE LOWER(varietal) LIKE '%%{varietal_name}%%' LIMIT 6"""
    data = mysql_engine.query_selector(query_sql)
    varietal_names = [result[0] for result in data]
    return varietal_names

@app.route('/suggest_regions')
def suggest_regions():
    country = request.args.get('country')
    input = request.args.get('input')
    suggestions = fetch_region_suggestions(country, input)
    return json.dumps(suggestions)

def fetch_region_suggestions(country, input):
    if country == "all":
        query_sql = f"""SELECT DISTINCT appellation FROM {MYSQL_DATABASE}.wine_data WHERE LOWER(appellation) LIKE '%%{input}%%' LIMIT 10"""
    else:
        query_sql = f"""SELECT DISTINCT appellation FROM {MYSQL_DATABASE}.wine_data WHERE LOWER(appellation) LIKE '%%{input}%%' AND LOWER(country)='{country}' LIMIT 10"""
    data = mysql_engine.query_selector(query_sql)
    region_names = [result[0].split()[0].rstrip(",") for result in data]
    return region_names


SimilarWines.initialize_cache()
app.run(debug=True)

