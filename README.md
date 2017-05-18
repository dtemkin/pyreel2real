# pyreel2real
A main repository for my various movie and tv show related works.



## Data



Data was collected and compiled using various sources. Each component and its usages
are as follows:

ID    Source          Usages
--    ---------       --------
1     Movielens       Recommender-Movielens
2     Fandango        Recommender-Custom
3     IMDB            Recommender-Custom; Rosy Ratings
4     OMDB            Recommender-Custom; Rosy Ratings
5     RogerEbert      Rosy Ratings
6     AlchemyAPI*     Rosy Ratings
7     Mashape*        Rosy Ratings

\       Description
        ------------
...     Data downloaded from 'goo.gl/j4g9c6'
...     Scrape of HTML Page containing movies currently in theaters filtered by location
...     Scrape of Awards and Main Page in order to collect Oscar Performance and Box Office data not included as part of OMDB
...     Simple wrapper for OMDB API
...     Scrape of HTML Page from 'rogerebert.com'
...     Wrapper for Text Sentiment Endpoint from AlchemyAPI
...     Wrapper for Mashape implementation of AlchemyAPI Text Sentiment

* interchangeable



## Projects



### Rosy Ratings



##### Description

My analysis of whether the star ratings assigned by movie review critics differed from the overall sentiment conveyed in the written portion of the review.
Data used was collected from IMDB and RogerEbert.com. AlchemyAPI was used for the text sentiment estimation.

The script is compatible with both a direct connection to AlchemiAPI through IBM Watson or through Mashape. Both are free but there are daily query limits imposed on Free User Accounts. For more information please refer to http://www.alchemyapi.com/api.

##### Findings

A more complete description of the project can be found on my blog: www.dtemkin.com/star_rating_bias </em>



### Recommender



#### Movielens

###### Description

My exploration of the movielens users dataset and predicting user movie preferences using
machine learning.

###### Findings


#### Custom - What I should see in theaters.

###### Description

My custom recommender uses a personally compiled list of movies to train a binary classification model
which is in turn applied to movies currently in theaters. The goal was to predict whether I "have watched"
or "have not watched" a particular film. However, for the sake of interpretation when I appled the
model to movies in theaters I considered the "have watched" prediction analogous to "should watch".

###### Findings

