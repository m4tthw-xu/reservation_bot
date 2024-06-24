import re
import nltk
from nltk.corpus import stopwords
from gensim.models import Word2Vec, FastText
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

import json

# Preprocess tXext function
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = text.strip()
    tokens = word_tokenize(text)
    tokens = [word for word in tokens if word not in stopwords.words('english')]
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    return tokens

def train_model():
    # Initialize an empty list to store the reviews
    reviews = []

    # Read the JSON data from the file and extract the first 10,000 reviews
    with open('yelp_academic_dataset_review.json', 'r', encoding='utf-8') as file:
        for i, line in enumerate(file):
            if i >= 1_000_000:  # Stop after the first 10,000 reviews
                break
            review = json.loads(line)
            clean_text = review['text'].replace('\n', ' ')  # Replace newline characters with spaces
            reviews.append(clean_text)

    # Print the number of reviews extracted to confirm
    print(f"Extracted {len(reviews)} reviews.")

    # Preprocess all reviews
    processed_reviews = [preprocess_text(review) for review in reviews]

    word2vec_model = Word2Vec(
        sentences=processed_reviews,
        vector_size=200,  # Increased vector size
        window=10,        # Larger context window
        min_count=5,      # Ignore less frequent words
        workers=4,        # Number of CPU threads
        sg=1,             # Using Skip-gram
        epochs=10         # Increased epochs
    )
    word2vec_model.save("word2vec_restaurant.model")

def find_similarity(word1, word2):
    # Find similar words using Word2Vec
    word2vec_model = Word2Vec.load("similarity_model/word2vec_restaurant.model")
    # similar_words = word2vec_model.wv.most_similar('tofu', topn=100)
    # print("Word2Vec similar words to 'tofu':", similar_words)

    try:
        similarity_value = word2vec_model.wv.similarity(word1, word2)
    except:
        return -1
    return similarity_value


print(f"Association between 'chinese' and 'dumpling': {find_similarity('chinese', 'dumpling')}")
