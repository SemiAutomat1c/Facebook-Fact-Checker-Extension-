import spacy
from langdetect import detect
from textblob import TextBlob
from transformers import pipeline

# load NLP models
nlp = spacy.load("en_core_web_sm")

sentiment_model = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment"
)

emotion_model = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    top_k=None
)

def analyze_text(text):

    result = {}

    # 1️⃣ detect language
    lang = detect(text)
    result["language"] = lang

    # 2️⃣ clean and parse text
    doc = nlp(text)

    tokens = [token.text for token in doc if not token.is_stop and not token.is_punct]
    result["tokens"] = tokens

    # 3️⃣ named entities
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    result["entities"] = entities

    # 4️⃣ sentiment
    sentiment = sentiment_model(text)[0]
    result["sentiment"] = sentiment

    # 5️⃣ emotion detection
    emotions = emotion_model(text)[0]
    result["emotions"] = emotions

    # 6️⃣ polarity score
    blob = TextBlob(text)
    result["polarity"] = blob.sentiment.polarity
    result["subjectivity"] = blob.sentiment.subjectivity

    return result


text = input("Enter text: ")

analysis = analyze_text(text)

print("\nNLP ANALYSIS\n")

for k,v in analysis.items():
    print(k, ":", v)