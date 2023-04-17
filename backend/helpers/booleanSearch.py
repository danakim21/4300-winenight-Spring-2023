import re

def boolean_search(data, keys, keywords):
    results = []
    for d in data:
        review = d[keys.index('review')]

        # Count exact matches
        num_exact_matches = sum(len(re.findall(r'\b{}\b'.format(keyword), review, re.IGNORECASE)) for keyword in keywords)

        # Count substring matches
        num_substring_matches = sum(len(re.findall(r'{}'.format(keyword), review, re.IGNORECASE)) for keyword in keywords)

        # Subtract exact matches from substring matches to avoid double counting
        num_substring_matches -= num_exact_matches

        if num_exact_matches > 0 or num_substring_matches > 0:
            d_with_matches = dict(zip(keys, d))

            # Assign higher weight to exact matches (e.g., 2) and a lower weight to substring matches (e.g., 1)
            total_score = num_exact_matches * 2 + num_substring_matches

            d_with_matches['num_exact_matches'] = num_exact_matches
            d_with_matches['num_substring_matches'] = num_substring_matches
            d_with_matches['total_score'] = total_score
            results.append(d_with_matches)

    # Sort results based on the total_score
    results.sort(key=lambda x: x['total_score'], reverse=True)
    return results