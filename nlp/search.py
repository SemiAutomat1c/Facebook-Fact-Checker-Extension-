import json
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer, util

# download nltk data
nltk.download("punkt")
nltk.download("stopwords")

stop_words = set(stopwords.words("english"))

# -------------------------
# PREPROCESS FUNCTION
# -------------------------
def preprocess(text):

    # normalize
    text = text.lower()

    # remove punctuation
    text = re.sub(r"[^a-zA-Z\s]", "", text)

    # tokenize
    tokens = word_tokenize(text)

    # remove stopwords
    tokens = [w for w in tokens if w not in stop_words]

    return " ".join(tokens)


# -------------------------
# LOAD DATASET
# -------------------------
def load_news():

    with open("news.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    titles = []

    for article in data:
        titles.append(article["title"])

    return titles


# -------------------------
# TFIDF FEATURE EXTRACTION
# -------------------------
def tfidf_features(titles):

    vectorizer = TfidfVectorizer()

    matrix = vectorizer.fit_transform(titles)

    return vectorizer, matrix


# -------------------------
# EMBEDDING MODEL
# -------------------------
print("Loading embedding model...")

model = SentenceTransformer("all-MiniLM-L6-v2")


# -------------------------
# FACT CHECK FUNCTION
# -------------------------
def verify_title(user_title, dataset):

    clean_title = preprocess(user_title)

    # embeddings
    user_embedding = model.encode(clean_title, convert_to_tensor=True)
    dataset_embeddings = model.encode(dataset, convert_to_tensor=True)

    # cosine similarity
    scores = util.cos_sim(user_embedding, dataset_embeddings)[0]

    best_index = scores.argmax().item()
    best_score = scores[best_index].item()

    return dataset[best_index], best_score


# -------------------------
# MAIN PROGRAM
# -------------------------
def main():

    print("\nLoading news dataset...")

    dataset = load_news()

    clean_dataset = [preprocess(title) for title in dataset]

    # build tfidf (optional but part of pipeline)
    vectorizer, matrix = tfidf_features(clean_dataset)

    print("Dataset loaded:", len(dataset), "articles")

    print("\nEnter a news title to verify\n")

    while True:

        title = input("Title: ")

        if title.lower() == "exit":
            break

        best_match, score = verify_title(title, clean_dataset)

        print("\nMost Similar News:")
        print(best_match)

        print("Similarity Score:", round(score, 3))

        if score > 0.75:
            print("Result: Likely REAL news")
        elif score > 0.55:
            print("Result: Possibly related news")
        else:
            print("Result: No strong match (Possible misinformation)")

        print("-" * 50)


# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    main()