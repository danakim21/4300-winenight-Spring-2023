# Cosine Similarity Logic from A4
import time
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
    _reviews_cache = None
    _tokenized_reviews_cache = None
    _idx_to_wine_name = None
    _inverted_index_cache = None
    _idf_cache = None
    _doc_norms_cache = None

    def __init__(self, wine_name, liked_wines, disliked_wines):
        start_time = time.time()
        self.wine_name = wine_name

        if SimilarWines._reviews_cache is None:
            SimilarWines._reviews_cache = self.get_all_reviews()

        if SimilarWines._tokenized_reviews_cache is None:    
            SimilarWines._tokenized_reviews_cache, SimilarWines._idx_to_wine_name = self.get_all_reviews_tokenized()

        if SimilarWines._inverted_index_cache is None:
            SimilarWines._inverted_index_cache = self.build_inverted_index(SimilarWines._tokenized_reviews_cache)

        if SimilarWines._idf_cache is None:
            SimilarWines._idf_cache = self.compute_idf(SimilarWines._inverted_index_cache, len(SimilarWines._tokenized_reviews_cache))

        if SimilarWines._doc_norms_cache is None:
            SimilarWines._doc_norms_cache = self.compute_doc_norms(SimilarWines._inverted_index_cache, SimilarWines._idf_cache, len(SimilarWines._tokenized_reviews_cache))

        self.reviews_non_tokenized = SimilarWines._reviews_cache
        self.reviews = SimilarWines._tokenized_reviews_cache
        self.inverted_index = SimilarWines._inverted_index_cache
        self.idf = SimilarWines._idf_cache
        self.doc_norms = SimilarWines._doc_norms_cache

        self.wine_name_to_wine_idx = {v: k for k, v in SimilarWines._idx_to_wine_name.items()}
        self.liked_wines = liked_wines
        self.disliked_wines = disliked_wines
        self.wine_term_matrix = np.zeros([len(self.reviews_non_tokenized), len(self.inverted_index)])
        self.term_idx_to_term = {}
        for term_idx, (term, tup_list) in enumerate(self.inverted_index.items()):
            for (wine_idx, count) in tup_list:
                self.wine_term_matrix[wine_idx][term_idx] = count
            self.term_idx_to_term[term_idx] = term
        
        self.query = self.getQuery(wine_name)
        self.search_results = self.index_search(self.query, self.inverted_index, self.idf, self.doc_norms)
        mysql_engine.load_file_into_db("../init.sql")
        end_time = time.time()
        print("Time taken for INIT: {:.4f} seconds".format(end_time - start_time))

    @classmethod
    def initialize_cache(cls):
        if cls._reviews_cache is None:
            cls._reviews_cache = cls.get_all_reviews()

        if cls._tokenized_reviews_cache is None:
            cls._tokenized_reviews_cache, cls._idx_to_wine_name = cls.get_all_reviews_tokenized()

    def get_similarity_scores(self, limit=None):
        start_time = time.time()
        if limit is None:
            limit = len(self.search_results)
        else:
            limit = min(limit, len(self.search_results))

        wine_ids = [msg_id for _, msg_id in self.search_results[1:limit]]
        wine_metadata_list = self.get_wines_metadata(wine_ids)

        scored_wines = []

        for score, wine_metadata in zip(self.search_results[1:limit], wine_metadata_list):
            wine_name = wine_metadata["wine_name"]
            price = wine_metadata["price"]
            category = wine_metadata["category"]
            varietal = wine_metadata["varietal"]
            appellation = wine_metadata["appellation"]
            country = wine_metadata["country"]
            review = wine_metadata["review"]

            scored_wines.append({
                "score": score[0],
                "wine_name": wine_name,
                "price": price,
                "category": category,
                "varietal": varietal,
                "appellation": appellation,
                "country": country,
                "review": review
            })

        end_time = time.time()
        print("Time taken for get_similarity_scores: {:.4f} seconds".format(end_time - start_time))
        return scored_wines

    
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
    
    @classmethod
    def get_all_reviews(cls):
        start_time = time.time()
        query_sql = f"""SELECT wine, review FROM {MYSQL_DATABASE}.wine_data"""
        data = mysql_engine.query_selector(query_sql)
        reviews = {d[0]: d[1] for d in data}
        end_time = time.time()
        print("Time taken for get_all_reviews: {:.4f} seconds".format(end_time - start_time))
        return reviews
    
    def get_wines_metadata(self, wine_ids):
        start_time = time.time()
        wine_names = [self.get_wine_name_from_id(msg_id) for msg_id in wine_ids]
        wine_names_str = "', '".join([wine_name.replace("'", "''").replace("%", "%%") for wine_name in wine_names])
        query_sql = f"""SELECT wine, price, category, varietal, appellation, country, review FROM {MYSQL_DATABASE}.wine_data WHERE wine IN ('{wine_names_str}')"""
        cursor = mysql_engine.query_selector(query_sql)
        wine_metadata_dict = {}

        for wine_name, price, category, varietal, appellation, country, review in cursor:
            wine_metadata_dict[wine_name] = {
                "wine_name": wine_name,
                "price": price,
                "category": category,
                "varietal": varietal,
                "appellation": appellation,
                "country": country,
                "review": review
            }

        # Sort the wine metadata list based on the order of the input wine names
        wine_metadata_list = [wine_metadata_dict[wine_name] for wine_name in wine_names]

        end_time = time.time()
        print("Time taken for get_wines_metadata: {:.4f} seconds".format(end_time - start_time))
        return wine_metadata_list
        
    @classmethod
    def get_all_reviews_tokenized(cls):
        start_time = time.time()

        # reviews = list(cls._reviews_cache.values())
        # idx_to_wine_name = dict(enumerate(cls._reviews_cache.keys()))
        reviews = []
        idx_to_wine_name = {}
        for idx, (wine_name, review) in enumerate(cls._reviews_cache.items()):
            reviews.append(review)
            idx_to_wine_name[idx] = wine_name
        tokenized_reviews = [cls.tokenize(review) for review in reviews]
        end_time = time.time()
        print("Time taken for reviews_tokenized: {:.4f} seconds".format(end_time - start_time))
        return tokenized_reviews, idx_to_wine_name

    
    def get_wine_name_from_id(self, msg_id):
        return list(self.reviews_non_tokenized.keys())[msg_id]
    
    def build_inverted_index(self, tokenized_reviews):
        start_time = time.time()

        inverted_index = {}
        for i, review in enumerate(tokenized_reviews):
            # Use Counter to count term occurrences in the review
            term_counts = Counter(review)
            for term, count in term_counts.items():
                inverted_index.setdefault(term, []).append((i, count))

        # No need to sort inverted_index[term] as it's already sorted

        end_time = time.time()
        print("Time taken for build_inverted_index: {:.4f} seconds".format(end_time - start_time))
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
        start_time = time.time()
        # if query is None:
        #     return []
        
        # If either the liked wines list or the disliked wines list is non-empty, use rocchio
        if len(self.liked_wines) > 0 or len(self.disliked_wines) > 0:
            rocchio = self.get_rocchio_vector(self.wine_name, self.liked_wines, self.disliked_wines, self.wine_term_matrix, self.wine_name_to_wine_idx)
            rocchio = rocchio.tolist()
            query_word_counts = {}
            for term_idx, word_count in enumerate(rocchio):
                query_word_counts[self.term_idx_to_term[term_idx]] = word_count
        elif query is not None:
            # Tokenize query
            query_words = tokenizer.tokenize(query.lower())
            query_word_counts = {}
            for word in query_words:
                query_word_counts[word] = query_word_counts.get(word, 0) + 1
        else:
            return []

        # Compute dot products
        doc_scores = score_func(self, query_word_counts, index, idf)
        
        # Get normalized query
        norm_sum = 0
        for word in query_word_counts:
            if word in idf:
                norm_sum += (query_word_counts[word] * idf[word])**2
        
        query_norm = np.sqrt(norm_sum)
        if query_norm == 0:
            query_norm = 1
        
        # Normalize scores
        for doc_id in doc_scores:
            doc_scores[doc_id] /= (query_norm * doc_norms[doc_id])
            # doc_scores[doc_id] = np.log(doc_scores[doc_id]) - np.log(query_norm) - np.log(doc_norms[doc_id])
        
        # Return sorted results
        results = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        results = [(score, doc_id) for doc_id, score in results]

        end_time = time.time()
        print("Time taken for index_search: {:.4f} seconds".format(end_time - start_time))
            
        return results
    
    def getQuery(self, wine_name):
        # Construct query to get review for given wine name
        start_time = time.time()

        wine_name = wine_name.replace("'", "''")
        query_sql = f"""SELECT review FROM {MYSQL_DATABASE}.wine_data WHERE wine = '{wine_name}'"""        
        cursor = mysql_engine.query_selector(query_sql)

        # Iterate over cursor to get review text
        end_time = time.time()
        print("Time taken for QUERY: {:.4f} seconds".format(end_time - start_time))
        data = cursor.fetchone()
        if data is not None:
            review = data[0]
            return review
        else:
            return None
        
        
        
    def get_rocchio_vector(self, query, relevant, irrelevant, input_doc_matrix, \
            wine_name_to_index, a=1, b=1, c=9999999999999999, clip = True):
        
        start_time = time.time()

        if query == "null" or query is None:
            query_vec = np.zeros_like(input_doc_matrix[0,:])
        else:
            query_vec = input_doc_matrix[wine_name_to_index[query], :]
        relevant_update_vec, irrelevant_update_vec = np.zeros_like(query_vec), np.zeros_like(query_vec) 
        num_relevant, num_irrelevant = len(relevant), len(irrelevant)
        
        if num_relevant > 0:
            for rel_name in relevant:
                relevant_update_vec += input_doc_matrix[wine_name_to_index[rel_name], :]
            relevant_update_vec = (b / float(num_relevant)) * relevant_update_vec

        if num_irrelevant > 0:
            for irrel_name in irrelevant:
                irrelevant_update_vec += input_doc_matrix[wine_name_to_index[irrel_name], :]
            irrelevant_update_vec = (c / float(num_irrelevant)) * irrelevant_update_vec
        
        rocchio = a * query_vec + relevant_update_vec - irrelevant_update_vec
        if clip:
            np.clip(rocchio, 0, None, out=rocchio)

        end_time = time.time()
        print("Time taken for ROCCHIO: {:.4f} seconds".format(end_time - start_time))

        return rocchio