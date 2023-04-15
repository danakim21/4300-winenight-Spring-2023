# Cosine Similarity Logic from A4

import re
import logging
import sys
import os
import math
import numpy as np
from collections import Counter
from nltk.tokenize import TreebankWordTokenizer as tt

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db import mysql_engine, MYSQL_DATABASE

class SimilarWines:
    def __init__(self, wine_name):
        self.reviews_non_tokenized = self.get_all_reviews()
        self.reviews = self.get_all_reviews_tokenized()
        self.inverted_index = self.build_inverted_index(self.reviews)
        self.idf = self.compute_idf(self.inverted_index, len(self.reviews))
        self.doc_norms = self.compute_doc_norms(self.inverted_index, self.idf, len(self.reviews))
        self.query = self.getQuery(wine_name)
        self.search_results = self.index_search(self.query, self.inverted_index, self.idf, self.doc_norms)
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
    
    def get_all_reviews(self):
        query_sql = f"""SELECT wine, review FROM {MYSQL_DATABASE}.wine_data"""
        data = mysql_engine.query_selector(query_sql)
        reviews = {d[0]: d[1] for d in data}
        return reviews
    
    def get_wine_metadata(self, wine_name):
        query_sql = f"""SELECT price, category, varietal, appellation, country FROM {MYSQL_DATABASE}.wine_data WHERE wine = '{wine_name}'"""
        cursor = mysql_engine.query_selector(query_sql)

        # Iterate over cursor to get review text
        data = cursor.fetchone()
        if data is not None:
            price, category, varietal, appellation, country = data
            return {
                "price": price,
                "category": category,
                "varietal": varietal,
                "appellation": appellation,
                "country": country
            }
        else:
            return None
        
    def get_all_reviews_tokenized(self):
        reviews = list(self.reviews_non_tokenized.values())
        tokenized_reviews = [self.tokenize(review) for review in reviews]
        return tokenized_reviews
    
    def get_wine_name_from_id(self, msg_id):
        return list(self.reviews_non_tokenized.keys())[msg_id]
    
    def build_inverted_index(self, tokenized_reviews):
        inverted_index = {}
        
        for i, review in enumerate(tokenized_reviews):
            for term in set(review):
                inverted_index.setdefault(term, []).append((i, review.count(term)))
                
        for term in inverted_index:
            inverted_index[term].sort()
            
        return inverted_index
    
    def compute_idf(self, inv_idx, n_docs, min_df=200, max_df_ratio=0.2):
        idf = {}
    
        for term in inv_idx:
            df = len(inv_idx[term])
            
            # Ignore ignore all terms that occur in strictly fewer than min_df documents
            # Ignore all words that occur in more than max_df_ratio of the documents.
            if df < min_df or df / n_docs > max_df_ratio:
                continue
                
            idf[term] = math.log2(n_docs / (1 + df))
            
        return idf
    
    def compute_doc_norms(self, index, idf, n_docs):
        inv_index = {key: val for key, val in index.items()
           if key in idf}
        norms = np.zeros(n_docs)
    
        for term in inv_index.keys():
            if term not in idf:
                continue
            for doc_id, tf in inv_index[term]:
                norms[doc_id] += (tf * idf[term]) ** 2
                
        norms = np.sqrt(norms)
        
        return norms
    
    def accumulate_dot_scores(self, query_word_counts, index, idf):
        doc_scores = {}
    
        for term in query_word_counts.keys():
            if term in index:
                for doc_id, tf in index[term]:
                    if term in idf:
                        q_i = query_word_counts[term] * idf[term]
                        d_ij = tf * idf[term]
                    else:
                        q_i = 0
                        d_ij = 0

                    if doc_id not in doc_scores:
                        doc_scores[doc_id] = 0

                    doc_scores[doc_id] += q_i * d_ij
                    
        return doc_scores
    
    def index_search(self, query, index, idf, doc_norms, score_func=accumulate_dot_scores, tokenizer=tt()):
        # Tokenize query
        query_words = tokenizer.tokenize(query.lower())
        
        query_word_counts = {}
        for word in query_words:
            query_word_counts[word] = query_word_counts.get(word, 0) + 1
        
        # Compute dot products
        doc_scores = score_func(self, query_word_counts, index, idf)
        
        # Get normalized query
        norm_sum = 0
        for word in query_word_counts:
            if word in idf:
                norm_sum += (query_word_counts[word] * idf[word])**2
        
        query_norm = np.sqrt(norm_sum)
        
        # Normalize scores
        for doc_id in doc_scores:
            doc_scores[doc_id] /= (query_norm * doc_norms[doc_id])
        
        # Return sorted results
        results = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        results = [(score, doc_id) for doc_id, score in results]
            
        return results
    
    def getQuery(self, wine_name):
        # Construct query to get review for given wine name
        query_sql = f"""SELECT review FROM {MYSQL_DATABASE}.wine_data WHERE wine = '{wine_name}'"""        
        cursor = mysql_engine.query_selector(query_sql)

        # Iterate over cursor to get review text
        data = cursor.fetchone()
        if data is not None:
            review = data[0]
            return review
        else:
            return None