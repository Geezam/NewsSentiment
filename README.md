# NewsSentiment

A Python project that scrapes news headlines from RSS feeds, performs sentiment analysis using Vader, and generates a static HTML report that can be automatically deployed to Netlify.

Sentiment Analysis uses AI and natural language processing (NLP) to analyze text data and determine the emotional tone, such as positive, negative, or neutral. 

This project is designed to run in two stages:
1.  **Scraping:** Fetches new articles, performs sentiment analysis, and saves the results to rolling CSV files (keeping the latest 100 articles per source).
2.  **Reporting:** Reads all CSVs, generates a `rich` report for the terminal, saves that report as `index.html`, and deploys it to Netlify.

## Features

* Fetches articles from a customizable dictionary of RSS feeds (`engine.py`).
* Performs sentiment analysis on headlines using `vaderSentiment`.
* Saves articles to individual CSV files (e.g., `csv/Jamaica_Gleaner.csv`).
* Automatically manages data by keeping only the latest 100 articles per source.
* Generates a beautiful terminal-based report with `rich`, showing sentiment breakdown by percentage.
* Exports the `rich` report to a self-contained `index.html` file, ready for web hosting.
* Includes a function to automatically deploy the final `index.html` to Netlify using their API.
* Uses a robust fallback system (Feedparser > Requests) to handle tricky feeds.

