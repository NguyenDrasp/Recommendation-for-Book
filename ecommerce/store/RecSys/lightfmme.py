import os
import random
import numpy as np
import pandas as pd
from scipy import sparse

import lightfm
from lightfm import LightFM, cross_validation
from lightfm.evaluation import precision_at_k, auc_score

from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


def create_interaction_matrix(df,user_col, item_col, rating_col, norm= False, threshold = None):
    '''
    Function to create an interaction matrix dataframe from transactional type interactions
    Required Input -
        - df = Pandas DataFrame containing user-item interactions
        - user_col = column name containing user's identifier
        - item_col = column name containing item's identifier
        - rating col = column name containing user feedback on interaction with a given item
        - norm (optional) = True if a normalization of ratings is needed
        - threshold (required if norm = True) = value above which the rating is favorable
    Expected output - 
        - Pandas dataframe with user-item interactions ready to be fed in a recommendation algorithm
    '''
    interactions = df.groupby([user_col, item_col])[rating_col] \
            .sum().unstack().reset_index(). \
            fillna(0).set_index(user_col)
    if norm:
        interactions = interactions.applymap(lambda x: 1 if x > threshold else 0)
    return interactions

def create_user_dict(interactions):
    '''
    Function to create a user dictionary based on their index and number in interaction dataset
    Required Input - 
        interactions - dataset create by create_interaction_matrix
    Expected Output -
        user_dict - Dictionary type output containing interaction_index as key and user_id as value
    '''
    user_id = list(interactions.index)
    user_dict = {}
    counter = 0 
    for i in user_id:
        user_dict[i] = counter
        counter += 1
    return user_dict

def create_item_dict(df,id_col,name_col):
    '''
    Function to create an item dictionary based on their item_id and item name
    Required Input - 
        - df = Pandas dataframe with Item information
        - id_col = Column name containing unique identifier for an item
        - name_col = Column name containing name of the item
    Expected Output -
        item_dict = Dictionary type output containing item_id as key and item_name as value
    '''
    item_dict ={}
    for i in range(df.shape[0]):
        item_dict[(df.loc[i,id_col])] = df.loc[i,name_col]
    return item_dict

def runMF(interactions, n_components=30, loss='warp', k=15, epoch=30,n_jobs = 4):
    '''
    Function to run matrix-factorization algorithm
    Required Input -
        - interactions = dataset create by create_interaction_matrix
        - n_components = number of embeddings you want to create to define Item and user
        - loss = loss function other options are logistic, brp
        - epoch = number of epochs to run 
        - n_jobs = number of cores used for execution 
    Expected Output  -
        Model - Trained model
    '''
    
    #uncommented for train test split
    x = sparse.csr_matrix(interactions.values)
    model = LightFM(no_components= n_components, loss=loss,k=k)
    model.fit(x,epochs=epoch,num_threads = n_jobs)
    return model


def sample_recommendation_user(model, interactions, user_id, user_dict, 
                               item_dict,threshold = 0,nrec_items = 10, show = True):
    '''
    Function to produce user recommendations
    Required Input - 
        - model = Trained matrix factorization model
        - interactions = dataset used for training the model
        - user_id = user ID for which we need to generate recommendation
        - user_dict = Dictionary type input containing interaction_index as key and user_id as value
        - item_dict = Dictionary type input containing item_id as key and item_name as value
        - threshold = value above which the rating is favorable in new interaction matrix
        - nrec_items = Number of output recommendation needed
    Expected Output - 
        - Prints list of items the given user has already bought
        - Prints list of N recommended items  which user hopefully will be interested in
    '''
    n_users, n_items = interactions.shape
    user_x = user_dict[user_id]
    scores = pd.Series(model.predict(user_x,np.arange(n_items)))
    
    scores.index = interactions.columns
    print(scores.index)
    scores = list(pd.Series(scores.sort_values(ascending=False).index))
        
    print(scores)   
    known_items = list(pd.Series(interactions.loc[user_id,:] \
                                 [interactions.loc[user_id,:] > threshold].index) \
                       .sort_values(ascending=False))

    scores = [x for x in scores if x not in known_items]
    return_score_list = scores[0:nrec_items]
    known_items = list(pd.Series(known_items).apply(lambda x: item_dict[x]))
    scores = list(pd.Series(return_score_list).apply(lambda x: item_dict[x]))
    
    return scores

def similar_items(item_id, N):
    """Function to return top N similar items
    based on https://github.com/lyst/lightfm/issues/244#issuecomment-355305681
    Args:
        item_id (int): id of item to be used as reference
        item_features (scipy sparse CSR matrix): item feature matric
        model (LightFM instance): fitted LightFM model
        N (int): Number of top similar items to return
    Returns:
        pandas.DataFrame: top N most similar items with score
    """
    _, item_representations = model.get_item_representations()
    try:
      item_id_matrix = interactions.columns.get_loc(item_id)
    except:
      return []
    # Cosine similarity
    scores = item_representations.dot(item_representations[item_id_matrix, :])
    item_norms = np.linalg.norm(item_representations, axis=1)
    item_norms[item_norms == 0] = 1e-10
    scores /= item_norms
    best = np.argpartition(scores, -(N + 1))[-(N + 1) :]
    ans = []
    for i in best:
      ans.append(interactions.columns[i])
    return ans

df_playlist = pd.read_csv('.\Data\Ratings.csv', low_memory=False,
                          error_bad_lines=False, 
                          warn_bad_lines=False,
                          skiprows=lambda i: i>0 and random.random() > 0.50)

df_playlist = df_playlist.groupby('ISBN').filter(lambda x: len(x)>=100)
df_playlist = df_playlist[df_playlist.groupby('User-ID').ISBN.transform('nunique')>=10]

interactions = create_interaction_matrix(df = df_playlist, user_col = "User-ID", item_col = 'ISBN', rating_col = 'Book-Rating', norm= False, threshold = None)
user_dict = create_user_dict(interactions=interactions)
df_item=pd.read_csv('.\Data\Books.csv', low_memory=False)
item_dict = create_item_dict(df=df_item, id_col='ISBN', name_col='Book-Title')
model = runMF(interactions = interactions,
                 n_components = 30,
                 loss = 'warp',
                 k = 15,
                 epoch = 30,
                 n_jobs = 4)




