async function analyzeSentiment() {
  const text = document.getElementById("inputText").value;
  const resultBox = document.getElementById("result");

  if (!text.trim()) {
    resultBox.innerHTML = "<p>Please enter some text.</p>";
    return;
  }

  resultBox.innerHTML = "<p>Analyzing...</p>";

  const response = await fetch("/analyze/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });

  const data = await response.json();

  resultBox.innerHTML = `
    <h3>Results:</h3>
    <p><strong>Text:</strong> ${data.text}</p>
    <p><strong>VADER Sentiment:</strong> ${data.vader.sentiment}</p>
    <p><strong>VADER Score:</strong> ${data.vader.score.toFixed(3)}</p>
    <p><strong>TextBlob Sentiment:</strong> ${data.textblob.sentiment}</p>
    <p><strong>TextBlob Polarity:</strong> ${data.textblob.polarity.toFixed(3)}</p>
  `;
}
