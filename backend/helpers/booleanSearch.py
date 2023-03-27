import re

def boolean_search(data, keys, keywords):
    results = []
    for d in data:
        review = d[keys.index('review')]
        num_matches = sum(len(re.findall(r'\b{}\b'.format(keyword), review, re.IGNORECASE)) for keyword in keywords)
        if num_matches > 0:
            d_with_matches = dict(zip(keys, d))
            d_with_matches['num_matches'] = num_matches
            results.append(d_with_matches)
    results.sort(key=lambda x: x['num_matches'], reverse=True)
    return results

