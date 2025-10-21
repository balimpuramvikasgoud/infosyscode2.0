from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

app = FastAPI()

# Mount static folder (path corrected to be relative to main.py)
app.mount("/static", StaticFiles(directory="static"), name="static")

analyzer = SentimentIntensityAnalyzer()

class TextInput(BaseModel):
    text: str

@app.post("/analyze/")
async def analyze_sentiment(data: TextInput):
    text = data.text

    # VADER
    vader_result = analyzer.polarity_scores(text)
    vader_sentiment = (
        "Positive" if vader_result["compound"] > 0.05
        else "Negative" if vader_result["compound"] < -0.05
        else "Neutral"
    )

    # TextBlob
    blob = TextBlob(text)
    blob_polarity = blob.sentiment.polarity
    blob_sentiment = (
        "Positive" if blob_polarity > 0
        else "Negative" if blob_polarity < 0
        else "Neutral"
    )

    return {
        "text": text,
        "vader": {"sentiment": vader_sentiment, "score": vader_result["compound"]},
        "textblob": {"sentiment": blob_sentiment, "polarity": blob_polarity},
    }


@app.get("/", response_class=HTMLResponse)
async def serve_homepage():
    # Open the file (path corrected to be relative to main.py)
    with open("static/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)