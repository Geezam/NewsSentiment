from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import feedparser
import requests
import time
import urllib3
import ssl
import os
import socket
from functions import (load_seen_links, save_seen_link, save_and_prune_csv,
                       sanitize_filename, generate_sentiment_report)
from engine import RSS_FEEDS, HEADERS, USER_AGENT, BAR_CHAR, MAX_BAR_WIDTH


if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
        getattr(ssl, '_create_unverified_context', None)):
    print("Disabling global SSL certificate verification for feedparser...")
    ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
analyzer = SentimentIntensityAnalyzer()
new_articles_found = 0
seen_links = load_seen_links()

for feed_title, feed_url in RSS_FEEDS.items():

    print(f"\nChecking Feed: {feed_title} ({feed_url})")
    feed = None

    output_filename = sanitize_filename(feed_title)

    try:
        print("Attempt 1: Trying feedparser direct parse...")
        socket.setdefaulttimeout(25)
        feed = feedparser.parse(feed_url, agent=USER_AGENT)
        socket.setdefaulttimeout(None)

        if not hasattr(feed, 'status'):
            print("[ERROR] Feed failed to parse (Timeout or DNS Error). "
                  "No status found.")
            continue

        if ((feed.status >= 300 and feed.status < 400) or
            feed.status == 403 or
           (feed.status >= 500 and feed.status < 600)):
            print(f"Attempt 1 FAILED (Status: {feed.status}). "
                  "Trying requests fallback")
            response = requests.get(feed_url, headers=HEADERS,
                                    timeout=25, verify=False)

            if response.status_code != 200:
                print(f"Attempt 2 FAILED. status: {response.status_code}")
                continue

            print("Attempt 2 SUCCESSFUL. Parsing content")
            feed = feedparser.parse(response.content)

        elif feed.status != 200:
            print(f"[ERROR] Failed to fetch feed. Server: {feed.status}")
            continue

        if feed.bozo:
            print(f"[ERROR] Feed is malformed. Error: {feed.bozo_exception}")
            continue

        if not feed.entries:
            print("[Warning] Feed parsed successfully, no entries were found.")
            continue

        print(f"Feed parsed successfully. Output file: {output_filename}")

        for entry in feed.entries:
            headline = entry.title
            link = entry.link

            pub_time_struct = entry.get('published_parsed',
                                        entry.get('updated_parsed',
                                                  time.gmtime()))

            pub_date_str = time.strftime('%Y-%m-%d %H:%M:%S', pub_time_struct)

            if link not in seen_links:
                new_articles_found += 1
                sentiment = analyzer.polarity_scores(headline)

                compound = sentiment['compound']
                if compound >= 0.05:
                    label = "Positive"
                elif compound <= -0.05:
                    label = "Negative"
                else:
                    label = "Neutral"

                new_article_data = {
                    "Published": pub_date_str,
                    "Headline": headline,
                    "Link": link,
                    "Source": feed_title,
                    "Sentiment": label,
                    "Compound": compound,
                    "Positive": sentiment['pos'],
                    "Negative": sentiment['neg'],
                    "Neutral": sentiment['neu']
                }

                print(f"\n  [NEW] Headline: {headline}")
                print(f"  Link: {link}")
                print(f"  Sentiment: {sentiment}")
                print(f"  Saving to {output_filename} (and pruning to 100)")

                seen_links.add(link)
                save_seen_link(link)

                save_and_prune_csv(output_filename, new_article_data,
                                   max_rows=100)
            else:
                pass

    except requests.exceptions.RequestException as e:
        print(f"[CRITICAL ERROR] Network request (Attempt 2) failed: {e}")
    except Exception as e:
        print(f"[UNEXPECTED SCRIPT ERROR] {e}")

print(f"Found {new_articles_found} new articles.")

generate_sentiment_report(BAR_CHAR, MAX_BAR_WIDTH)
