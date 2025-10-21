from fastapi import (
    FastAPI, Request, Form, File, 
    UploadFile, HTTPException
)
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob  # <-- RE-ENABLED
import csv
import io
import nltk  # <-- RE-ENABLED
from contextlib import asynccontextmanager

# --- LIFESPAN EVENT: Runs on server startup to load models ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # This code runs ONCE when the server starts
    print("Server starting up...")
    print("Downloading NLTK data (this might take a moment)...")
    
    # Download required NLTK data for TextBlob
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('brown', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)
    except Exception as e:
        print(f"Error downloading NLTK data: {e}. This might be a network issue.")

    # "Warm up" the models by loading them once
    print("Warming up sentiment models...")
    global analyzer # Make analyzer global
    analyzer = SentimentIntensityAnalyzer()  # Load VADER
    TextBlob("test").sentiment  # Load TextBlob models
    
    print("NLTK data and models are ready. Server startup complete.")
    
    yield
    
    # This code runs when the server shuts down
    print("Server shutting down...")

# --- Create FastAPI App ---
app = FastAPI(lifespan=lifespan) 

# Mount static folder
app.mount("/static", StaticFiles(directory="static"), name="static")


# --- Pydantic Model for Text (Fast) ---
class TextInput(BaseModel):
    text: str

# --- HELPER: Analyze a single piece of text ---
def analyze_single_text(text: str):
    # VADER
    vader_result = analyzer.polarity_scores(text)
    vader_sentiment = (
        "Positive" if vader_result["compound"] > 0.05
        else "Negative" if vader_result["compound"] < -0.05
        else "Neutral"
    )

    # TextBlob (RE-ENABLED)
    blob = TextBlob(text)
    blob_polarity = blob.sentiment.polarity
    blob_sentiment = (
        "Positive" if blob_polarity > 0
        else "Negative" if blob_polarity < 0
        else "Neutral"
    )
    
    display_text = (text[:250] + "...") if len(text) > 250 else text

    return {
        "type": "single_result",
        "text": display_text,
        "vader": {"sentiment": vader_sentiment, "score": vader_result["compound"]},
        "textblob": {"sentiment": blob_sentiment, "polarity": blob_polarity},
    }

# --- HELPER: Analyze a CSV file ---
def analyze_csv_file(contents: bytes):
    try:
        decoded_content = contents.decode('utf-8')
    except UnicodeDecodeError:
        decoded_content = contents.decode('latin-1')
        
    csv_reader = csv.DictReader(io.StringIO(decoded_content))
    
    vader_scores = []
    blob_polarities = [] # <-- RE-ENABLED
    positive_count, negative_count, neutral_count = 0, 0, 0
    reviews_processed = 0
    
    review_column_name = None
    if not csv_reader.fieldnames:
         raise HTTPException(status_code=400, detail="CSV is empty or unreadable.")
    for name in ["reviewText", "review", "text", "Review", "Text"]:
        if name in csv_reader.fieldnames:
            review_column_name = name
            break
    if not review_column_name:
        raise HTTPException(status_code=400, detail=f"Could not find a review column (e.g., 'reviewText'). Found: {csv_reader.fieldnames}")

    for row in csv_reader:
        text = row.get(review_column_name)
        if text:
            reviews_processed += 1
            # VADER
            vader_result = analyzer.polarity_scores(text)
            vader_scores.append(vader_result["compound"])
            
            # TextBlob (RE-ENABLED)
            blob = TextBlob(text)
            blob_polarities.append(blob.sentiment.polarity)

            # Tally counts (using VADER)
            if vader_result["compound"] > 0.05: positive_count += 1
            elif vader_result["compound"] < -0.05: negative_count += 1
            else: neutral_count += 1

    if reviews_processed == 0:
        raise HTTPException(status_code=400, detail="CSV file processed, but no text was found in the review column.")

    avg_vader = sum(vader_scores) / reviews_processed
    avg_blob = sum(blob_polarities) / reviews_processed # <-- RE-ENABLED
    
    return {
        "type": "csv_summary",
        "reviews_processed": reviews_processed,
        "average_vader_score": avg_vader,
        "average_textblob_polarity": avg_blob, # <-- RE-ENABLED
        "positive_reviews": positive_count,
        "negative_reviews": negative_count,
        "neutral_reviews": neutral_count,
    }

# --- ENDPOINT 1: For text analysis ---
@app.post("/analyze-text/")
async def analyze_sentiment_text(data: TextInput):
    # This calls the helper which now does both
    return analyze_single_text(data.text)

# --- ENDPOINT 2: For file analysis ---
@app.post("/analyze-file/")
async def analyze_sentiment_file(file_input: UploadFile = File(...)):
    contents = await file_input.read()
    filename = file_input.filename
    
    if not contents:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    if filename.endswith(".csv"):
        result = analyze_csv_file(contents)
        result["filename"] = filename
        return result
    elif filename.endswith(".txt"):
        result = analyze_single_text(contents.decode("utf-8"))
        result["filename"] = filename
        return result
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a .txt or .csv file.")

# --- Homepage Server ---
@app.get("/", response_class=HTMLResponse)
async def serve_homepage():
    with open("static/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)
