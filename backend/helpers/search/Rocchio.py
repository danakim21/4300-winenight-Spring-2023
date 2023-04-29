# Rocchio Logic from A5
import SimilarWines
import numpy as np

#### BEGIN INIT CLASS ####
sw = SimilarWines()
reviews = sw._reviews_cache # dict{wine_name(str) : review(str)}
wine_idx_to_wine_name = sw._idx_to_wine_name # dict{wine_idx(int) : wine_name(str)}
wine_name_to_wine_idx = {v: k for k, v in wine_idx_to_wine_name.items()}
inverted_index = sw._inverted_index_cache # dict{term(str) : (idx(int), count(int))}

wine_term_matrix = np.empty([len(reviews), len(inverted_index)])
for term_idx, (term, (wine_idx, count)) in enumerate(inverted_index.items()):
    wine_term_matrix[wine_idx][term_idx] = count
#### END INIT CLASS ####

def rocchio(query, relevant, irrelevant, input_doc_matrix, \
            wine_name_to_index, a=.3, b=.3, c=.8, clip = True):
    # too lazy to change "mov" variables to "wine" variables lol
    mov_idx = wine_name_to_index[query]
    query_vec = input_doc_matrix[mov_idx, :]
    relevant_update_vec, irrelevant_update_vec = np.zeros_like(query_vec), np.zeros_like(query_vec) 
    num_relevant, num_irrelevant = len(relevant), len(irrelevant)
    
    if num_relevant > 0:
        for rel_mov_name in relevant:
            relevant_update_vec += input_doc_matrix[wine_name_to_index[rel_mov_name], :]
        relevant_update_vec = (b / float(num_relevant)) * relevant_update_vec
        
    if num_irrelevant > 0:
        for irrel_mov_name in irrelevant:
            irrelevant_update_vec += input_doc_matrix[wine_name_to_index[irrel_mov_name], :]
        irrelevant_update_vec = (c / float(num_irrelevant)) * irrelevant_update_vec
    
    rocchio = a * query_vec + relevant_update_vec - irrelevant_update_vec
    if clip:
        np.clip(rocchio, 0, None, out=rocchio)
    return rocchio

# TODO:
### get list of relevant wine names from likedWines() in base.html
### get list of irrelevant wine names from dislikedWines in base.html
### cosine similarity with new rocchio leveraging SimilarWines.py
### track if there has been any user input -- then we switch to rocchio permanently