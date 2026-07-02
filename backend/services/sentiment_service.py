"""
=============================================================
SENTIMENT ANALYSIS SERVICE
=============================================================
Analyzes restaurant reviews to determine customer sentiment.

USES TWO ANALYZERS:
1. VADER (Valence Aware Dictionary and sEntiment Reasoner)
   - Best for social media / short text
   - Returns compound score: -1 (negative) to +1 (positive)
   
2. TextBlob (as fallback)
   - Returns polarity: -1 to +1
   - Returns subjectivity: 0 (objective) to 1 (subjective)

HOW SENTIMENT IS CLASSIFIED:
- compound > 0.05  → Positive
- compound < -0.05 → Negative
- otherwise        → Neutral

TOP COMPLAINTS EXTRACTION:
We look at negative reviews and extract common complaint phrases.
=============================================================
"""

from database import reviews_collection

# Try to import VADER; fall back to TextBlob if unavailable
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    vader_analyzer = SentimentIntensityAnalyzer()
    USE_VADER = True
except ImportError:
    USE_VADER = False

try:
    from textblob import TextBlob
    USE_TEXTBLOB = True
except ImportError:
    USE_TEXTBLOB = False


# -------------------------------------------------------
# Common complaint keywords to look for in negative reviews
# -------------------------------------------------------
COMPLAINT_KEYWORDS = [
    "cold food", "late delivery", "slow delivery", "wrong order",
    "bad taste", "stale", "overpriced", "too spicy", "undercooked",
    "missing items", "rude delivery", "unhygienic", "soggy",
    "small portions", "bad packaging", "leaked", "hair in food",
    "raw food", "oily", "tasteless", "expired"
]


def analyze_sentiment(text: str):
    """
    Analyze the sentiment of a single review text.
    
    Args:
        text: The review text to analyze
    
    Returns:
        dict with sentiment label and scores
    """
    if USE_VADER:
        scores = vader_analyzer.polarity_scores(text)
        compound = scores["compound"]

        if compound > 0.05:
            label = "positive"
        elif compound < -0.05:
            label = "negative"
        else:
            label = "neutral"

        return {
            "label": label,
            "compound": compound,
            "pos": scores["pos"],
            "neg": scores["neg"],
            "neu": scores["neu"]
        }

    elif USE_TEXTBLOB:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity

        if polarity > 0.1:
            label = "positive"
        elif polarity < -0.1:
            label = "negative"
        else:
            label = "neutral"

        return {
            "label": label,
            "compound": polarity,
            "pos": max(polarity, 0),
            "neg": abs(min(polarity, 0)),
            "neu": 1 - abs(polarity)
        }

    else:
        # No NLP library available → return neutral
        return {
            "label": "neutral",
            "compound": 0.0,
            "pos": 0.0,
            "neg": 0.0,
            "neu": 1.0
        }


def extract_complaints(text: str):
    """
    Check a review text for common complaint keywords.
    
    Args:
        text: The review text
    
    Returns:
        List of complaint keywords found in the text
    """
    text_lower = text.lower()
    found = []
    for keyword in COMPLAINT_KEYWORDS:
        if keyword in text_lower:
            found.append(keyword)
    return found


def get_restaurant_sentiment(restaurant_id: str):
    """
    Analyze all reviews for a restaurant and return a sentiment summary.
    
    PROCESS:
    1. Fetch all reviews for the restaurant
    2. Run sentiment analysis on each review
    3. Count positive / negative / neutral
    4. Calculate percentages
    5. Extract top complaints from negative reviews
    6. Calculate average rating
    
    Args:
        restaurant_id: The restaurant to analyze
    
    Returns:
        dict with sentiment breakdown and top complaints
    """
    # Fetch all reviews for this restaurant
    reviews = list(
        reviews_collection.find(
            {"restaurant_id": restaurant_id},
            {"_id": 0}
        )
    )

    total = len(reviews)

    if total == 0:
        return {
            "restaurant_id": restaurant_id,
            "total_reviews": 0,
            "positive_pct": 0.0,
            "negative_pct": 0.0,
            "neutral_pct": 0.0,
            "average_rating": 0.0,
            "top_complaints": []
        }

    # Counters
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    total_rating = 0.0
    all_complaints = {}

    for review in reviews:
        review_text = review.get("review_text", "")
        rating = review.get("rating", 0)
        total_rating += rating

        # Analyze sentiment
        sentiment = analyze_sentiment(review_text)

        if sentiment["label"] == "positive":
            positive_count += 1
        elif sentiment["label"] == "negative":
            negative_count += 1
            # Extract complaints from negative reviews
            complaints = extract_complaints(review_text)
            for complaint in complaints:
                all_complaints[complaint] = all_complaints.get(complaint, 0) + 1
        else:
            neutral_count += 1

    # Calculate percentages
    positive_pct = round((positive_count / total) * 100, 1)
    negative_pct = round((negative_count / total) * 100, 1)
    neutral_pct = round((neutral_count / total) * 100, 1)
    average_rating = round(total_rating / total, 1)

    # Sort complaints by frequency and take top 5
    top_complaints = sorted(
        all_complaints.keys(),
        key=lambda k: all_complaints[k],
        reverse=True
    )[:5]

    return {
        "restaurant_id": restaurant_id,
        "total_reviews": total,
        "positive_pct": positive_pct,
        "negative_pct": negative_pct,
        "neutral_pct": neutral_pct,
        "average_rating": average_rating,
        "top_complaints": top_complaints
    }
