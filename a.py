import json
import re
from collections import Counter

def extract_keywords(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    
    # Comprehensive keyword list organized by category
    keywords = {
        # Middle East / Iran-Israel
        "iran": ["iran", "tehran", "persian", "ayatollah"],
        "israel": ["israel", "tel aviv", "netanyahu", "zionist"],
        "strike": ["strike", "airstrike", "bomb", "attack", "missile"],
        "spy": ["spy", "espionage", "intelligence", "mossad"],
        "arrest": ["arrest", "detain", "jail", "prison", "custody"],
        
        # Philippines / Southeast Asia
        "philippines": ["philippines", "filipino", "manila", "duterte", "marcos", "sona"],
        "china": ["china", "beijing", "chinese", "south china sea", "west philippine sea"],
        "territory": ["territory", "dispute", "sovereignty", "maritime", "claims"],
        
        # Global / General
        "foreign": ["foreign", "international", "diplomatic", "embassy", "consulate"],
        "military": ["military", "army", "navy", "air force", "defense", "troops"],
        "government": ["government", "official", "administration", "authority", "regime"],
        "protest": ["protest", "demonstration", "rally", "unrest", "riot"],
        "election": ["election", "vote", "poll", "ballot", "campaign"],
        "economy": ["economy", "economic", "inflation", "recession", "gdp", "market"],
        "health": ["health", "pandemic", "virus", "vaccine", "hospital", "covid"],
        "climate": ["climate", "environment", "pollution", "emissions", "green"],
        "technology": ["technology", "cyber", "digital", "ai", "artificial intelligence"],
        "crime": ["crime", "criminal", "illegal", "fraud", "corruption"],
        "accident": ["accident", "disaster", "tragedy", "casualty", "fatal"],
        "death": ["death", "die", "killed", "dead", "fatalities"],
        "rights": ["rights", "human rights", "freedom", "democracy", "justice"],
        
        # People / Titles
        "president": ["president", "prime minister", "leader", "minister", "official"],
        "reporter": ["reporter", "journalist", "news", "media", "press"],
        
        # Organizations
        "united nations": ["united nations", "un", "security council", "international court"],
        "white house": ["white house", "pentagon", "capitol", "congress"],
        
        # Time indicators (helps with recency)
        "recent": ["recent", "today", "yesterday", "this week", "breaking"],
    }
    
    # Flatten keywords for extraction while keeping track of categories
    all_keywords = []
    keyword_to_category = {}
    
    for category, words in keywords.items():
        for word in words:
            all_keywords.append(word)
            keyword_to_category[word] = category
    
    found = []
    found_categories = set()
    
    # Find individual keyword matches
    for k in all_keywords:
        if k in text and k not in found:
            found.append(k)
            found_categories.add(keyword_to_category[k])
    
    return found, list(found_categories), keyword_to_category

def calculate_relevance_score(claim_keywords, article_text, keyword_to_category):
    """
    Calculate a more sophisticated relevance score
    """
    score = 0
    matched_details = []
    
    # Count keyword matches (weighted by uniqueness)
    keyword_matches = []
    for keyword in claim_keywords:
        if keyword in article_text:
            keyword_matches.append(keyword)
            # Base score for match
            score += 1
            
            # Bonus for longer/more specific keywords
            if len(keyword.split()) > 1:  # Multi-word phrases
                score += 1
                matched_details.append(f"Phrase match: '{keyword}'")
    
    # Check for category diversity (different topics covered)
    categories_matched = set()
    for keyword in keyword_matches:
        categories_matched.add(keyword_to_category.get(keyword, "other"))
    
    category_bonus = len(categories_matched)
    if category_bonus > 1:
        score += category_bonus - 1  # Bonus for covering multiple topics
        matched_details.append(f"Multiple topics: {', '.join(categories_matched)}")
    
    # Check for title matches (keywords in title are more important)
    title_text = article_text.split("content")[0] if "content" in article_text else article_text[:500]
    title_keywords = [k for k in keyword_matches if k in title_text]
    if title_keywords:
        title_bonus = len(title_keywords)
        score += title_bonus
        matched_details.append(f"Keywords in title: {', '.join(title_keywords)}")
    
    return score, matched_details, keyword_matches, list(categories_matched)

# Load the JSON file
with open("ScrapedNews/Scraped/gma.json", "r", encoding="utf-8") as f:
    content = f.read()
    # Remove the JavaScript wrapper
    start = content.find('{')
    end = content.rfind('}') + 1
    json_content = content[start:end]
    data = json.loads(json_content)

# Display available articles for reference
print("\n" + "="*80)
print("📚 AVAILABLE ARTICLES IN DATABASE")
print("="*80)
for i, r in enumerate(data["results"][:5]):  # Show first 5 articles
    title = r.get("titleNoFormatting", r.get("title", "No title"))[:70]
    source = r.get("visibleUrl", "unknown")
    print(f"{i+1}. [{source}] {title}...")
print("..." if len(data["results"]) > 5 else "")
print("="*80)

# Get user claim
claim = input("\n🔍 Enter your claim: ")

# Extract keywords and categories
claim_keywords, claim_categories, keyword_to_category = extract_keywords(claim)

print("\n" + "="*60)
print("📊 CLAIM ANALYSIS")
print("="*60)
print(f"Claim: {claim}")
print(f"Keywords detected: {', '.join(claim_keywords) if claim_keywords else 'None'}")
print(f"Topics detected: {', '.join(claim_categories) if claim_categories else 'None'}")
print("="*60)

# Analyze all articles
all_results = []

for i, r in enumerate(data["results"]):
    # Combine title and content
    title = r.get("titleNoFormatting", r.get("title", ""))
    content = r.get("contentNoFormatting", r.get("content", ""))
    full_text = (title + " " + content).lower()
    source = r.get("visibleUrl", "Unknown")
    url = r.get("unescapedUrl", r.get("url", "N/A"))
    
    # Calculate relevance score
    score, match_details, matched_keywords, matched_categories = calculate_relevance_score(
        claim_keywords, full_text, keyword_to_category
    )
    
    if score > 0:
        all_results.append({
            "index": i,
            "score": score,
            "title": title,
            "source": source,
            "url": url,
            "matched_keywords": matched_keywords,
            "matched_categories": matched_categories,
            "match_details": match_details
        })

# Sort by score (highest first)
all_results.sort(key=lambda x: x["score"], reverse=True)

# Display results
print("\n" + "="*80)
print(f"📋 MATCHING ARTICLES (found {len(all_results)} relevant articles)")
print("="*80)

if all_results:
    best = all_results[0]
    
    # Determine verdict based on score and category match
    verdict = "UNVERIFIED"
    confidence = "LOW"
    
    if best["score"] >= 5:
        verdict = "STRONG FACT"
        confidence = "HIGH"
    elif best["score"] >= 3:
        verdict = "FACT"
        confidence = "MEDIUM"
    elif best["score"] >= 1:
        # Check if categories match
        common_cats = set(best["matched_categories"]).intersection(set(claim_categories))
        if common_cats:
            verdict = "PARTIALLY FACT"
            confidence = "LOW-MEDIUM"
    
    print(f"\n🏆 BEST MATCH (Confidence: {confidence} | Score: {best['score']})")
    print(f"   Verdict: {verdict}")
    print(f"   Source: {best['source']}")
    print(f"   Title: {best['title'][:100]}")
    print(f"   URL: {best['url']}")
    print(f"   Matched keywords: {', '.join(best['matched_keywords'])}")
    print(f"   Matched topics: {', '.join(best['matched_categories'])}")
    
    if best["match_details"]:
        print("\n   🔍 Match details:")
        for detail in best["match_details"][:3]:  # Show top 3 details
            print(f"      • {detail}")
    
    # Show other strong matches
    if len(all_results) > 1:
        print("\n" + "-"*40)
        print("📌 OTHER RELEVANT ARTICLES:")
        for article in all_results[1:4]:  # Show next 3 matches
            print(f"\n   • Score {article['score']}: {article['title'][:70]}...")
            print(f"     Keywords: {', '.join(article['matched_keywords'][:3])}")
            print(f"     Source: {article['source']}")
else:
    print("\n❌ No relevant articles found matching your claim.")
    print("   The claim may be UNVERIFIED based on current database.")

print("\n" + "="*80)
print("📝 VERDICT KEY:")
print("   STRONG FACT: High confidence match (score ≥ 5)")
print("   FACT: Good match (score ≥ 3)")
print("   PARTIALLY FACT: Some keyword overlap but limited evidence")
print("   UNVERIFIED: Insufficient evidence in database")
print("="*80)