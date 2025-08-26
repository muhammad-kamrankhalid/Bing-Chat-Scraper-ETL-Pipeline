# Bing Chat Scraper & ETL Pipeline

## 📌 Overview
This project was developed as part of my **Python Internship assessment task** at infoSync.  
The goal was to design and implement a **real-time web scraping and ETL pipeline** that:
- Automates interactions with a chat interface (Bing Chat or a local simulation)
- Collects query–response pairs
- Applies rate limiting to avoid bot detection
- Transforms raw scraped data
- Loads the processed data into CSV and SQLite for analysis

---

## ⚙️ Features
- **Selenium Automation** → Simulates user interactions (typing, sending queries, waiting for responses)
- **BeautifulSoup Parsing** → Extracts structured data from rendered HTML
- **ETL Pipeline**:
  - **Extract** → Scrape queries & responses  
  - **Transform** → Clean, add metadata, validate responses  
  - **Load** → Save results in CSV, JSON, and SQLite database
- **Anti-Detection** → Human-like typing, random delays, polite rate limiting
- **Error Handling** → Timeout detection & fallback strategies

---

## 🛠️ Tech Stack
- Python 3.10+
- Selenium + WebDriver Manager
- BeautifulSoup4
- Pandas
- SQLAlchemy (SQLite)
- Flask (for local chat demo server)

---

## 🚀 How It Works
1. Start the **local chat demo server**:
   ```bash
   python chat_server.py
