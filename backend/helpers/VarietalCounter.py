import re
import logging
import sys
import os
from collections import Counter, defaultdict
import nltk
from nltk.corpus import stopwords

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db import mysql_engine, MYSQL_DATABASE

class VarietalCounter:
    def __init__(self):
        self.varietals = self.get_all_varietals()
        self.varietal_counts = self.get_varietal_counts_sorted()
        mysql_engine.load_file_into_db("../init.sql")

    @staticmethod
    def tokenize(text):
        """Returns a list of words that make up the text.
        
        Note: for simplicity, lowercase everything.
        Requirement: Use Regex to satisfy this function
        
        Params: {text: String}
        Returns: List
        """
        text = text.lower()
        result = re.findall(r'\b[^\W\d]+\b', text)
        
        return result

    def get_all_varietals(self):
        query_sql = f"""SELECT varietal FROM {MYSQL_DATABASE}.wine_data"""
        data = mysql_engine.query_selector(query_sql)
        reviews = [d[0] for d in data]
        tokenized_reviews = [self.tokenize(review) for review in reviews]
        return tokenized_reviews
    
    def get_varietal_counts_sorted(self):
        all_varietals = []
        for varietal in self.varietals:
            all_varietals.extend(varietal)
        varietal_counts = dict(Counter(all_varietals))
        sorted_counts = dict(sorted(varietal_counts.items(), key=lambda x: x[1], reverse=True))
        return sorted_counts
    
    def get_varietal_counts(self):
        varietal_counts = self.varietal_counts
        return varietal_counts
    
    def print_varietal_counts(self):
        # reverse the dictionary
        new_dict = defaultdict(list)
        for varietal, count in self.varietal_counts.items():
            new_dict[count].append(varietal)
        # print sorted varietals
        for count, varietal in new_dict.items():
            sorted_varietals = sorted(new_dict[count])
            print(str(count) + ": " + ', '.join(sorted_varietals))

