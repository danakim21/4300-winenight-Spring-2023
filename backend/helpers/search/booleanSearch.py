from collections import defaultdict
import re

def boolean_search(data, keywords, similarity_scores=None, flavorSearch=None):
    results = []

    if similarity_scores:
        similarity_scores_dict = {wine['wine_name']: wine['score'] for wine in similarity_scores}
    else:
        similarity_scores_dict = {}
    
    for d in data:
        review = d['review']

        # Count exact matches
        num_exact_matches = sum(len(re.findall(r'\b{}\b'.format(keyword), review, re.IGNORECASE)) for keyword in keywords)

        # Count substring matches
        num_substring_matches = sum(len(re.findall(r'{}'.format(keyword), review, re.IGNORECASE)) for keyword in keywords)

        # Subtract exact matches from substring matches to avoid double counting
        num_substring_matches -= num_exact_matches

        if num_exact_matches > 0 or num_substring_matches > 0:
            d_with_matches = d.copy()

            term_score = (num_exact_matches + num_substring_matches)

            # Incorporate similarity score into the total_score
            if flavorSearch:
                wine_name = d_with_matches["wine"]
            else:
                wine_name = d_with_matches["wine_name"]

            if wine_name in similarity_scores_dict:
                combined_score = term_score + similarity_scores_dict[wine_name]

            d_with_matches['num_exact_matches'] = num_exact_matches
            d_with_matches['num_substring_matches'] = num_substring_matches
            d_with_matches['term_score'] = term_score

            if not flavorSearch:
                d_with_matches['combined_score'] = combined_score
            results.append(d_with_matches)

    # Sort results based on the total_score
    if similarity_scores and flavorSearch:
        results.sort(key=lambda x: x['combined_score'], reverse=True)
    elif similarity_scores:
        results.sort(key=lambda x: x['score'], reverse=True)
    else:
        results.sort(key=lambda x: x['term_score'], reverse=True)
    return results