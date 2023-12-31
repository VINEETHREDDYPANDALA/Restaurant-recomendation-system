# -*- coding: utf-8 -*-
"""Restaurant recommendation

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1l874i44HiSC-U3qWiBl0RLgoLGXMd1Go
"""

!pip install geopandas

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords
from sklearn.metrics.pairwise import linear_kernel
from nltk.tokenize import WordPunctTokenizer
import webbrowser
import re
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import geopandas as gpd
import folium
from folium.plugins import HeatMap
from geopy.geocoders import Nominatim
import sklearn
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import accuracy_score

import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')
STOPWORDS = set(stopwords.words('english'))

# !pip install missingno

#loading the data
zomato_data = pd.read_csv('/content/drive/MyDrive/Datasets/RestaurantRecommendationSystem/zomato.csv')

#sample data
zomato_data.head()

#overview of data
zomato_data.info()

zomato_data['url']

#statistical overview of data
zomato_data.describe()

#number of restaurants
print('number of restaurants')
len(zomato_data['name'].unique())

"""## Data cleaning"""

#dropping unnecessary columns
zomato_data.drop(['url','phone','dish_liked'],axis=1,inplace=True)

#checking duplicates
zomato_data.duplicated().sum()

zomato_data[zomato_data.duplicated(keep=False)]

#dropping duplicates
zomato_data.drop_duplicates(inplace=True)

#checking null values
zomato_data.isnull().sum()

#visualizing missing  values
import missingno
plt.figure(figsize=(5,5))
missingno.matrix(zomato_data,figsize=(7,7))
plt.show()

#dropping missing values
zomato_data.dropna(how='any',inplace=True)

#checking the data shape after primary cleaning
zomato_data.shape

#checking the columns in the data
zomato_data.columns

#adding average ratings column
# Adjust the column names
zomato_data.name = zomato_data.name.apply(lambda x:x.title())
zomato_data.online_order.replace(('Yes','No'),(True, False),inplace=True)
zomato_data.book_table.replace(('Yes','No'),(True, False),inplace=True)

#renaming the columns
zomato_data.rename(columns={'approx_cost(for two people)': 'cost', 'listed_in(type)': 'category','listed_in(city)':'city','rate':'ratings'}, inplace=True)

zomato_data['ratings']= zomato_data['ratings'].str.split('/').str[0]

zomato_data['ratings'].value_counts()

#removing the row with ratings as New and -
#there are special values present in the ratings column 'new'and '-'
zomato_data.drop(zomato_data[zomato_data.ratings=='NEW'].index, inplace=True)
zomato_data.drop(zomato_data[zomato_data.ratings=='-'].index, inplace=True)
zomato_data = zomato_data.astype({'ratings':'float'})

zomato_data['ratings'].unique()

## Adding average Rating column
restaurants = list(zomato_data['name'].unique())
zomato_data['average_rating'] = 0

for i in range(len(restaurants)):
    zomato_data['average_rating'][zomato_data['name'] == restaurants[i]] = zomato_data['ratings'][zomato_data['name'] == restaurants[i]].mean()

#number of restaurants
print('number of restaurants')
len(zomato_data['name'].unique())

zomato_data['cost'] = zomato_data['cost'].str.replace(',','')

zomato_data['cost'] = zomato_data['cost'].astype(int)

#checking how city and location are different
zomato_data['city'].unique()

zomato_data['location'].unique()

"""Text preprocessing"""

#sample records of reviews list and cuisines
zomato_data[['reviews_list', 'cuisines']].sample(10)

#lower casing the columns cuisine and reviews list
zomato_data["reviews_list"] = zomato_data["reviews_list"].str.lower()

#removing punctuations from the columns
def remove_punctuation(text):
  return re.sub(r'[^\w\s]', '', text)

zomato_data['reviews_list'] = zomato_data["reviews_list"].apply(lambda text: remove_punctuation(text))

#removing stop words
def remove_stopwords(text):
    """custom function to remove the stopwords"""
    return " ".join([word for word in str(text).split() if word not in STOPWORDS])

zomato_data["reviews_list"] = zomato_data["reviews_list"].apply(lambda text: remove_stopwords(text))

## Removal of URLS
def remove_urls(text):
    url_pattern = re.compile(r'https?://\S+|www\.\S+')
    return url_pattern.sub(r'', text)

zomato_data["reviews_list"] = zomato_data["reviews_list"].apply(lambda text: remove_urls(text))

zomato_data.head(10)

zomato_data['reviews_list'].head()

"""## Exploratory Data Analysis"""

plt.figure(figsize=(8,6))
sns.barplot(
    y='votes',
    x = 'city',
    data=zomato_data.nlargest(10, 'votes')
)
plt.xticks(rotation=30)
plt.show()

#distribution of ratings
sns.histplot(data=zomato_data, x="ratings",kde=False)
plt.xticks(np.arange(0,4,0.1 , dtype=float))
plt.title('distribution of ratings')
plt.show()

#type of restaurant
plt.figure(figsize=(10,5))
sns.countplot(x='category',data=zomato_data)
plt.xticks(rotation=45)
plt.show('countplot of type of restaurant')
plt.show()

#type of restaurant
plt.figure(figsize=(10,5))
sns.boxplot(x='category',y='cost',data=zomato_data)
plt.xticks(rotation=45)
plt.show('countplot of type of restaurant')
plt.show()

#type of restaurant
plt.figure(figsize=(10,5))
sns.violinplot(x='category',y='votes',hue='online_order',data=zomato_data)
plt.xticks(rotation=45)
plt.show('countplot of type of restaurant and the votes')
plt.show()

#type of restaurant
plt.figure(figsize=(10,5))
sns.violinplot(x='category',y='average_rating',hue='book_table',data=zomato_data)
plt.xticks(rotation=45)
plt.show('countplot of type of restaurant and the votes')
plt.show()

# drop unecessary columns
zomato_data=zomato_data.drop(['rest_type','menu_item', 'votes'],axis=1)

# Randomly sample 60% of your dataframe
zomato_percent = zomato_data.sample(frac=0.5)

zomato_percent.shape

zomato_percent.head()

"""TF-IDF vectorizer"""

zomato_percent.set_index('name', inplace=True)
indices = pd.Series(zomato_percent.index)

# Creating tf-idf matrix
tfidf = TfidfVectorizer(analyzer='word', ngram_range=(1, 2), min_df=0, stop_words='english')
tfidf_matrix = tfidf.fit_transform(zomato_percent['reviews_list'])

cosine_similarities = linear_kernel(tfidf_matrix, tfidf_matrix)
cosine_similarities

def recommend(name, cosine_similarities = cosine_similarities):

    # Create a list to put top restaurants
    recommend_restaurant = []

    # Find the index of the hotel entered
    idx = indices[indices == name].index[0]

    # Find the restaurants with a similar cosine-sim value and order them from bigges number
    score_series = pd.Series(cosine_similarities[idx]).sort_values(ascending=False)

    # Extract top 30 restaurant indexes with a similar cosine-sim value
    top30_indexes = list(score_series.iloc[0:31].index)

    # Names of the top 30 restaurants
    for each in top30_indexes:
        recommend_restaurant.append(list(zomato_percent.index)[each])

    # Creating the new data set to show similar restaurants
    df_new = pd.DataFrame(columns=['cuisines', 'average_rating', 'cost','category','address','location'])

    # Create the top 30 similar restaurants with some of their columns
    for each in recommend_restaurant:
        df_new = df_new.append(pd.DataFrame(zomato_percent[['cuisines','average_rating', 'cost','category','address','location']][zomato_percent.index == each].sample()))

    # Drop the same named restaurants and sort only the top 10 by the highest rating
    df_new = df_new.drop_duplicates(subset=['cuisines','average_rating', 'cost'], keep=False)
    df_new = df_new.sort_values(by='average_rating', ascending=False).head(10)

    print('TOP %s RESTAURANTS LIKE %s WITH SIMILAR REVIEWS: ' % (str(len(df_new)), name))

    return df_new

recommendations = recommend('Dal Tadkaa')
recommendations

# Extracting the Location Information Using the Geopy

locations = pd.DataFrame({"Name": recommendations['location'].unique()})
locations

locations['Name']=locations['Name'].apply(lambda x: "Bangaluru " + str(x)) # here I have used lamda function
# A lambda function is a small anonymous function.
lat_lon=[]
geolocator=Nominatim(user_agent="app")
for location in locations['Name']:
    location = geolocator.geocode(location)
    if location is None:
        lat_lon.append(np.nan)
    else:
        geo=(location.latitude,location.longitude)
        lat_lon.append(geo)

locations['geo_loc']=lat_lon
locations.to_csv('locations.csv',index=False)

locations["Name"]=locations['Name'].apply(lambda x :  x.replace("Bangaluru","")[1:])
locations.head()

locations[['lat', 'long']] = pd.DataFrame(locations['geo_loc'].tolist(), index=locations.index)

locations

locations_new = locations[['lat','long']]
points = locations_new.values.tolist()
points

map = folium.Map(location=[12.98807076915207, 77.60963866454284], zoom_start=10)

for point in points:
  folium.CircleMarker(point,radius = 5,color = 'red',fill = True).add_to(map)

map

"""# Singular Value Decomposition(SVD)



"""

zomato_data.groupby('name')['ratings'].count().sort_values(ascending=False).head()

rating_crosstab = zomato_data.pivot_table(values='ratings', index='city', columns='name', fill_value=0)
rating_crosstab.head()

# shape of the Utility matrix (original matrix)
rating_crosstab.shape

# Transpose the Utility matrix
X = rating_crosstab.values.T
X.shape

SVD = TruncatedSVD(n_components=12, random_state=17)
result_matrix = SVD.fit_transform(X)
result_matrix.shape

# PearsonR coef
corr_matrix = np.corrcoef(result_matrix)
corr_matrix.shape

restaurant_names = rating_crosstab.columns
restaurants_list = list(restaurant_names)

popular_rest = restaurants_list.index('Cafe Coffee Day')

# restaurant of interest
corr_popular_rest = corr_matrix[popular_rest]
corr_popular_rest.shape

recommendations = list(restaurant_names[(corr_popular_rest < 1.0) & (corr_popular_rest > 0.9)])
top_results=zomato_data[zomato_data.name.isin(recommendations[:10])]
# top_results

locations2 = pd.DataFrame({"Name": top_results['location'].unique()})
locations2

locations['Name']=locations2['Name'].apply(lambda x: "Bangaluru " + str(x)) # here I have used lamda function
# A lambda function is a small anonymous function.
lat_lon=[]
geolocator=Nominatim(user_agent="app")
for location in locations2['Name']:
    location = geolocator.geocode(location)
    if location is None:
        lat_lon.append(np.nan)
    else:
        geo=(location.latitude,location.longitude)
        lat_lon.append(geo)

locations2['geo_loc']=lat_lon
locations2.to_csv('locations2.csv',index=False)

locations2["Name"]=locations2['Name'].apply(lambda x :  x.replace("Bangaluru","")[1:])
locations2.head()

locations2[['lat', 'long']] = pd.DataFrame(locations2['geo_loc'].tolist(), index=locations.index)

locations_new2 = locations2[['lat','long']]
points2 = locations_new2.values.tolist()

map = folium.Map(location=[12.98807076915207, 77.60963866454284], zoom_start=10)

for point in points[:20]:
  folium.CircleMarker(point,radius = 5,color = 'red',fill = True).add_to(map)

map

