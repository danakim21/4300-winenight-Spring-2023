import json
import time
from helpers.search.SimilarWines import SimilarWines
from helpers.misc.FlavorTypoCorrector import FlavorTypoCorrector
from helpers.search.booleanSearch import boolean_search
from data_fetchers import (
    sql_search_reviews,
    fetch_wine_suggestions,
    fetch_varietal_suggestions,
    fetch_region_suggestions,
)

def wine_reviews_search(request):
    # Get user input 
    wine_name = request.args.get("wine_name")
    flavors = request.args.getlist("flavors")
    liked_wines = request.args.getlist("likedWines")
    disliked_wines =  request.args.getlist("dislikedWines")

    flavor_typo_corrector = FlavorTypoCorrector(3)
    flavors = flavor_typo_corrector.get_replaced_flavor_list(flavors)

    similarity_scores = None

    # Check if wine_name, liked wines, or disliked wines are provided
    if wine_name != "null" and not liked_wines and not disliked_wines:
        sw = SimilarWines(wine_name, liked_wines=liked_wines, disliked_wines=disliked_wines)
        similarity_scores = sw.get_similarity_scores(limit=500)

        # If flavors are also provided, filter the similarity_scores by flavors
        if len(flavors) > 0 and flavors[0] != '':
            wine_data = [item for item in similarity_scores]
            filtered_wine_data = boolean_search(wine_data, flavors, similarity_scores)
            similarity_scores = [{'wine_name': item['wine_name'], 'combined_score': item['combined_score'], 'score': item['score'], 'term_score': item['term_score']} for item in filtered_wine_data] 
    
    results = sql_search_reviews(request, similarity_scores)
    return results

def suggest_wines(request):
    input = request.args.get("input")
    suggestions = fetch_wine_suggestions(input)
    return json.dumps(suggestions)

def suggest_varietals(request):
    input = request.args.get('input')
    # Mood
    chill=request.args.get("chill")
    sad=request.args.get("sad")
    sexy=request.args.get("sexy")
    angry=request.args.get("angry")
    wild=request.args.get("wild")
    low=request.args.get("low")

    suggestions = fetch_varietal_suggestions(input, chill=="true", sad=="true", sexy=="true", angry=="true", wild=="true", low=="true")
    return json.dumps(suggestions)

def suggest_regions(request):
    country = request.args.get('country')
    input = request.args.get('input')
    suggestions = fetch_region_suggestions(country, input)
    return json.dumps(suggestions)