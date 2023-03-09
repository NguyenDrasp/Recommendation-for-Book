import numpy as np # linear algebra
import pandas as pd 
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import nltk
import re
import requests
import random
from nltk.corpus import stopwords
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer


def popular_book(df, n=100):
    rating_count = df.groupby("ISBN").count()["Book-Rating"].reset_index()
    rating_count.rename(columns={"Book-Rating":"NumberOfVotes"},inplace=True)
    rating_average=df.groupby("ISBN")["Book-Rating"].mean().reset_index()
    rating_average.rename(columns={"Book-Rating":"AverageRatings"},inplace=True)
    popularBooks=rating_count.merge(rating_average,on="ISBN")
    
    def weighted_rate(x):
        v=x["NumberOfVotes"]
        R=x["AverageRatings"]
        
        return ((v*R) + (m*C)) / (v+m)
        
    C=popularBooks["AverageRatings"].mean()
    m=popularBooks["NumberOfVotes"].quantile(0.90)
    
    popularBooks=popularBooks[popularBooks["NumberOfVotes"] >=250]
    popularBooks["Popularity"]=popularBooks.apply(weighted_rate,axis=1)
    popularBooks=popularBooks.sort_values(by="Popularity",ascending=False)
    return popularBooks[["ISBN","NumberOfVotes","AverageRatings","Popularity"]].reset_index(drop=True).head(n)
    
def item_based(df,ISBN):
    ISBN=str(ISBN)
    
    if ISBN in df['ISBN'].values:
        rating_count=pd.DataFrame(df["ISBN"].value_counts())
        rare_books=rating_count[rating_count["ISBN"]<=200].index
        common_books=df[~df["ISBN"].isin(rare_books)]
        
        if ISBN in rare_books:
            most_common=pd.Series(common_books["ISBN"].unique()).sample(3).values
            print("Can not Recommend for this book")
            return most_common[:5]
        else:
            common_books_pivot=common_books.pivot_table(index=["User-ID"],columns=["ISBN"],values="Book-Rating")
            title=common_books_pivot[ISBN]
            recommendation_df=pd.DataFrame(common_books_pivot.corrwith(title).sort_values(ascending=False)).reset_index(drop=False)
            
            if ISBN in [title for title in recommendation_df["ISBN"]]:
                recommendation_df=recommendation_df.drop(recommendation_df[recommendation_df["ISBN"]==ISBN].index[0])
                
            less_rating=[]
            for i in recommendation_df["ISBN"]:
                if df[df["ISBN"]==i]["Book-Rating"].mean() < 5:
                    less_rating.append(i)
            if recommendation_df.shape[0] - len(less_rating) > 5:
                recommendation_df=recommendation_df[~recommendation_df["ISBN"].isin(less_rating)]
                
            recommendation_df=recommendation_df[0:5]
            recommendation_df.columns=["ISBN","Correlation"]
            return recommendation_df['ISBN']
    else:
        print("❌ COULD NOT FIND ❌")


def users_choice(new_df, id):
    
    users_fav=new_df[new_df["User-ID"]==id].sort_values(["Book-Rating"],ascending=False)[0:5]
    return users_fav

def user_based(new_df,users_pivot,df,id):
    if id not in new_df["User-ID"].values:
        print("❌ User NOT FOUND ❌")
          
    else:
        index=np.where(users_pivot.index==id)[0][0]
        similarity=cosine_similarity(users_pivot)
        similar_users=list(enumerate(similarity[index]))
        similar_users = sorted(similar_users,key = lambda x:x[1],reverse=True)[0:5]
    
        user_rec=[]
    
        for i in similar_users:
                data=df[df["User-ID"]==users_pivot.index[i[0]]]
                user_rec.extend(list(data.drop_duplicates("User-ID")["User-ID"].values))
    return user_rec[0:5]

def common(new_df,user,user_id):
    x=new_df[new_df["User-ID"]==user_id]
    recommend_books=[]
    user=list(user)
    for i in user:
        y=new_df[(new_df["User-ID"]==i)]
        books=y.loc[~y["ISBN"].isin(x["ISBN"]),:]
        books=books.sort_values(["Book-Rating"],ascending=False)[0:5]
        recommend_books.extend(books["ISBN"].values)
        
    return recommend_books[0:5]



