import requests

# Your NewsAPI key
API_KEY = "7feed6ad114a41caba9bddb97a0710c3"

# Endpoint and parameters
url = "https://newsapi.org/v2/everything"
params = {
    "q": "bitcoin",
    "language": "en",
    "sortBy": "publishedAt",
    "pageSize": 5,
    "apiKey": API_KEY
}

# Make the request
response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    articles = data.get("articles", [])
    if not articles:
        print("No articles found.")
    else:
        for i, article in enumerate(articles, start=1):
            print(f"Article {i}:")
            print("Title      :", article.get("title"))
            print("Description:", article.get("description"))
            print("URL        :", article.get("url"))
            print("-" * 60)
else:
    print("Error:", response.status_code, response.text)