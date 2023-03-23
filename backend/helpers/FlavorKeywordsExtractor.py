import re
import logging
import sys
import os
from collections import Counter
import nltk
from nltk.corpus import stopwords

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db import mysql_engine, MYSQL_DATABASE

class FlavorKeywords:
    def __init__(self):
        self.reviews = self.get_all_reviews()
        self.word_counts = self.get_word_counts_sorted()
        self.flavor_words = self.get_flavor_words()
        mysql_engine.load_file_into_db("/Users/junekim/Desktop/SP 2023/CS 4300/4300-winenight-Spring-2023/wine_dataset.sql")

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

    def get_all_reviews(self):
        query_sql = f"""SELECT review FROM {MYSQL_DATABASE}.wine_data"""
        data = mysql_engine.query_selector(query_sql)
        reviews = [d[0] for d in data]
        tokenized_reviews = [self.tokenize(review) for review in reviews]
        return tokenized_reviews
    
    def get_word_counts_sorted(self):
        all_words = []
        for review in self.reviews:
            all_words.extend(review)
        word_counts = dict(Counter(all_words))
        sorted_word_counts = dict(sorted(word_counts.items(), key=lambda x: x[1], reverse=True))
        filtered_word_counts = {word: count for word, count in sorted_word_counts.items() if count >= 50}
        return filtered_word_counts
    
    def get_flavor_words(self):
        sorted_word_counts = self.word_counts
        stopwords_list = stopwords.words('english')
        flavor_words = [word for word, count in sorted_word_counts.items() if word not in stopwords_list]
        return flavor_words

