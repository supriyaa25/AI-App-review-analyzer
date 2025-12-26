# AI-Agent
AI-Powered App Review Trend Analyzer

An AI-driven Python project that automatically analyzes Google Play Store reviews to identify common user issues, complaints, and feature requests. The system extracts meaningful insights from unstructured review text and highlights trending problems to support data-driven product decisions.

📌 Problem Statement

Mobile applications receive thousands of user reviews daily. Manually reading and analyzing these reviews to understand customer pain points is inefficient and error-prone. This project solves that problem by automating review analysis using AI, making it faster and more scalable.

🎯 Project Objective

Automatically collect app reviews

Extract important user issues using AI

Consolidate similar topics

Identify trending problems and feature requests

Provide actionable insights for product improvement

🏗️ Architecture Overview
Google Play Store Reviews
          ↓
      scraper.py
 (Review Collection)
          ↓
  topic_extractor.py
 (AI Topic Extraction)
          ↓
topic_consolidator.py
 (Merge Similar Topics)
          ↓
 trend_analyzer.py
 (Trend & Frequency Analysis)
          ↓
     Final Insights

🗂️ Project Structure
├── main.py                  # Entry point – runs the full pipeline
├── scraper.py               # Scrapes app reviews from Google Play Store
├── topic_extractor.py       # Extracts issues using Generative AI
├── topic_consolidator.py    # Merges similar topics into categories
├── trend_analyzer.py        # Analyzes topic trends and frequency
├── seed_topics.json         # Predefined issue & feature categories
├── requirements.txt         # Project dependencies
├── .env                     # Environment variables (API keys)
├── .gitignore               # Git ignored files

🔧 Technologies Used

Python

Google Play Scraper

Generative AI (Google Generative AI)

Pandas & NumPy

Pydantic

Environment Variable Management (.env)

⚙️ Setup & Installation
1️⃣ Clone the Repository
git clone https://github.com/your-username/app-review-trend-analyzer.git
cd app-review-trend-analyzer

2️⃣ Create Virtual Environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

3️⃣ Install Dependencies
pip install -r requirements.txt

🔐 Environment Configuration

Create a .env file in the root directory:

GOOGLE_API_KEY=your_google_generative_ai_key


⚠️ Do not commit .env files to GitHub.

▶️ Run the Project
python main.py


This will:

Scrape app reviews

Extract issues using AI

Consolidate similar topics

Analyze trends and frequencies

📊 Output

List of common user issues

Consolidated topic categories

Trending complaints and feature requests

💡 Use Cases

Product management decision-making

Customer feedback analysis

UX and performance improvement

AI-based review analytics

⭐ Key Highlights

Modular and scalable architecture

Handles unstructured text data efficiently

Uses AI for real-world problem solving

Interview and industry-ready project

🚀 Future Enhancements

Dashboard visualization (Streamlit)

Sentiment analysis per topic

Multi-language review support

Time-based trend comparison

Export insights to CSV / database
