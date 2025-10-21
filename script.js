document.addEventListener("DOMContentLoaded", () => {
    
    // --- Get DOM Elements ---
    const textInput = document.getElementById("inputText");
    const fileInput = document.getElementById("fileInput");
    const analyzeButton = document.getElementById("analyzeButton");
    
    const resultsPlaceholder = document.getElementById("results-placeholder");
    const loaderArea = document.getElementById("loader-area");
    const singleResultArea = document.getElementById("single-result-area");
    const csvResultArea = document.getElementById("csv-result-area");

    const fileNameSpan = document.getElementById("file-name");

    // --- Add Event Listeners ---
    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            fileNameSpan.textContent = fileInput.files[0].name;
            textInput.disabled = true;
            textInput.value = ""; // Clear text input
        } else {
            fileNameSpan.textContent = "Upload a File (.txt or .csv)";
            textInput.disabled = false;
        }
    });

    textInput.addEventListener("input", () => {
        if (textInput.value) {
            fileInput.value = null; 
            fileNameSpan.textContent = "Upload a File (.txt or .csv)";
            fileInput.disabled = true;
        } else {
            fileInput.disabled = false;
        }
    });

    analyzeButton.addEventListener("click", analyzeSentiment);

    // --- Main Fetch Function ---
    async function analyzeSentiment() {
        const text = textInput.value;
        const file = fileInput.files[0];

        let endpoint = "";
        let requestOptions = {};

        // --- 1. Validate Input & Prepare Request ---
        if (file) {
            endpoint = "/analyze-file/";
            const formData = new FormData();
            formData.append("file_input", file);
            requestOptions = { method: "POST", body: formData };
        } else if (text.trim()) {
            endpoint = "/analyze-text/";
            requestOptions = {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: text }),
            };
        } else {
            alert("Please enter some text or upload a file.");
            return;
        }
        
        // --- 3. Show Loader & Clear Old Results ---
        resultsPlaceholder.style.display = "none";
        singleResultArea.innerHTML = "";
        csvResultArea.innerHTML = "";
        loaderArea.style.display = "flex"; // Show the loader
        
        // --- 4. Fetch from API ---
        try {
            const response = await fetch(endpoint, requestOptions);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Analysis failed");
            }
            
            // --- 5. Display Results ---
            loaderArea.style.display = "none"; // Hide the loader
            
            if (data.type === "single_result") {
                displaySingleResult(data);
            } else if (data.type === "csv_summary") {
                displayCsvResult(data);
            }

        } catch (error) {
            console.error("Error:", error);
            loaderArea.style.display = "none"; // Hide loader on error
            singleResultArea.innerHTML = `<p style="color: red; text-align: center;"><b>Error:</b> ${error.message}</p>`;
        }
        
        // --- 6. Reset Inputs ---
        resetInputs();
    }

    // --- Helper: Display Single Result ---
    function displaySingleResult(data) {
        const vaderClass = data.vader.sentiment.toLowerCase();
        const blobClass = data.textblob.sentiment.toLowerCase(); // <-- RE-ENABLED
        
        // This now creates BOTH cards
        let html = `
            <div class="sentiment-card"> 
                <div class="sentiment-header ${vaderClass}">
                    <h3>VADER Analysis</h3>
                </div>
                <div class="sentiment-body">
                    <div class="metric">
                        <div class="label">Sentiment</div>
                        <div class="value ${vaderClass}">${data.vader.sentiment}</div>
                    </div>
                    <div class="metric">
                        <div class="label">Compound Score</div>
                        <div class="value ${vaderClass}">${data.vader.score.toFixed(3)}</div>
                    </div>
                </div>
            </div>
            
            <div class="sentiment-card">
                <div class="sentiment-header ${blobClass}">
                    <h3>TextBlob Analysis</h3>
                </div>
                <div class="sentiment-body">
                    <div class="metric">
                        <div class="label">Sentiment</div>
                        <div class="value ${blobClass}">${data.textblob.sentiment}</div>
                    </div>
                    <div class="metric">
                        <div class="label">Polarity Score</div>
                        <div class="value ${blobClass}">${data.textblob.polarity.toFixed(3)}</div>
                    </div>
                </div>
            </div>
        `;
        
        singleResultArea.innerHTML = html;
    }

    // --- Helper: Display CSV Result ---
    function displayCsvResult(data) {
        // This row will now be added
        let textBlobRow = `
            <tr>
                <td>Avg. TextBlob Polarity</td>
                <td>${data.average_textblob_polarity.toFixed(3)}</td>
            </tr>
            `;

        csvResultArea.innerHTML = `
            <div class="csv-summary">
                <h3>CSV Summary: <span>${data.filename || 'summary.csv'}</span></h3>
                <p>Based on VADER & TextBlob analysis of <strong>${data.reviews_processed}</strong> reviews.</p>
                <table class="summary-table">
                    <tr><td>Reviews Processed</td><td>${data.reviews_processed}</td></tr>
                    <tr>
                        <td><span class="positive">■</span> Positive Reviews (VADER)</td>
                        <td class="positive">${data.positive_reviews}</td>
                    </tr>
                    <tr>
                        <td><span class="neutral">■</span> Neutral Reviews (VADER)</td>
                        <td class="neutral">${data.neutral_reviews}</td>
                    </tr>
                    <tr>
                        <td><span class="negative">■</span> Negative Reviews (VADER)</td>
                        <td class="negative">${data.negative_reviews}</td>
                    </tr>
                    <tr>
                        <td>Avg. VADER Score</td>
                        <td>${data.average_vader_score.toFixed(3)}</td>
                    </tr>
                    ${textBlobRow} 
                </table>
            </div>
        `;
    }
    
    // --- Helper: Reset Inputs ---
    function resetInputs() {
        textInput.value = "";
        fileInput.value = null;
        fileNameSpan.textContent = "Upload a File (.txt or .csv)";
        textInput.disabled = false;
        fileInput.disabled = false;
    }
});
