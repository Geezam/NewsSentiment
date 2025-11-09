import os
import csv
import re
import requests
import zipfile
import datetime
import pandas as pd
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.rule import Rule
from engine import RSS_FEEDS
from engine import NETLIFY_SITE_ID, NETLIFY_TOKEN, TRACKING_FILE


def load_seen_links():
    if not os.path.exists(TRACKING_FILE):
        return set()
    with open(TRACKING_FILE, 'r') as f:
        links = [line.strip() for line in f]
    if len(links) > 1000:
        with open(TRACKING_FILE, 'w') as f:
            f.write("")
        return set()
    else:
        return set(links)


def save_seen_link(link):
    with open(TRACKING_FILE, 'a') as f:
        f.write(link + "\n")


def sanitize_filename(name):
    # Remove any characters that aren't letters, numbers, spaces, or hyphens
    name = re.sub(r'[^\w\s-]', '', name).strip()
    # Replace spaces or hyphens with a single underscore
    name = re.sub(r'[\s-]+', '_', name)
    return f"csv/{name}.csv"


def save_and_prune_csv(filename, new_article_dict, max_rows=100):
    headers = ["Published", "Headline", "Link", "Source", "Sentiment",
               "Compound", "Positive", "Negative", "Neutral"]

    all_data = []

    if os.path.exists(filename):
        try:
            with open(filename, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    all_data.append(row)
        except Exception as e:
            print(f"[ERROR] Could not read {filename}: {e}")
            # If file is corrupt, overwrite it
            all_data = []

    all_data.append(new_article_dict)

    try:
        all_data.sort(key=lambda x: x['Published'], reverse=True)
    except KeyError:
        print(f"[ERROR] Sorting failed. {filename}?")
        pass

    pruned_data = all_data[:max_rows]

    # 6. Rewrite the file with the pruned data
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(pruned_data)
    except Exception as e:
        print(f"[ERROR] Could not write to {filename}: {e}")


def generate_sentiment_report(BAR_CHAR, MAX_BAR_WIDTH):

    console = Console(record=True, width=100)
    output_html_file = "index.html"

    console.print("[bold black]Sentiment_AL: Sentiment Analysis Report"
                  "[/bold black]\n", style="b")

    for feed_title in RSS_FEEDS.keys():

        # Use sanitize_filename (from this same file)
        csv_file = sanitize_filename(feed_title)

        if not os.path.exists(csv_file):
            console.print(Panel(f"No file found.\nExpected at: {csv_file}",
                                title=f"[bold]{feed_title}[/bold]",
                                style="yellow", border_style="yellow"))
            console.print("\n")
            continue

        try:
            df = pd.read_csv(csv_file)
            # Check for 'Sentiment' column in the dataframe
            if 'Sentiment' not in df.columns:
                console.print(f"[yellow]Skipping {csv_file}: 'Sentiment' "
                              "column missing.[/yellow]\n")
                continue

            sentiment_counts = df['Sentiment'].value_counts()

            data = {
                "Positive": float(sentiment_counts.get("Positive", 0)),
                "Neutral": float(sentiment_counts.get("Neutral", 0)),
                "Negative": float(sentiment_counts.get("Negative", 0)),
            }
            total = sum(data.values())

        except Exception as e:
            console.print(f"[red]Error processing {csv_file}: {e}[/red]\n")
            continue

        # Plotting logic
        max_count = max(data.values()) if data.values() else 1
        if max_count == 0:
            max_count = 1

        plot_text = Text("\n")

        for sentiment, count in data.items():

            if total == 0:
                percentage = 0.0
            else:
                percentage = (count / total) * 100

            bar_width = int((count / max_count) * MAX_BAR_WIDTH)
            bar = BAR_CHAR * bar_width

            color = ("green" if sentiment == "Positive"
                     else "yellow" if sentiment == "Neutral" else "red")

            label_part = f"{sentiment:<10} {percentage:>5.1f}% "

            plot_text.append(label_part, style="bold")
            plot_text.append(f"{bar}\n", style=color)

        console.print(Rule(f"[bold]{feed_title}[/bold] (last {int(total)} "
                           "articles)", style="black"))

        console.print(plot_text)
        console.print(Rule(style="black"))
        console.print("\n")

    try:
        html_content = console.export_html()
        with open(output_html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        console.print(f"[bold green]Report saved to {output_html_file}"
                      "[/bold green]")
        today_weekday = datetime.datetime.now().weekday()
        if today_weekday == 6:  # 6
            print("It's Sunday. Deploying sentiment report to Netlify")
            deploy_to_netlify(output_html_file, NETLIFY_SITE_ID, NETLIFY_TOKEN)
        else:
            print("It's not Sunday. Skipping Deployment to Netlify.")
    except Exception as e:
        console.print(f"[bold red]Error saving HTML: {e}[/bold red]")


def deploy_to_netlify(file_to_deploy, site_id, token):
    console = Console()
    zip_file_name = "deploy.zip"
    headers_file_name = "_headers"

    try:
        with open(headers_file_name, "w") as f:
            # This rule tells Netlify to serve your file as text/html
            f.write(f"/{os.path.basename(file_to_deploy)}\n")
            f.write("  Content-Type: text/html; charset=utf-8\n")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        return

    try:
        with zipfile.ZipFile(zip_file_name, 'w') as zf:
            zf.write(file_to_deploy, os.path.basename(file_to_deploy))
            zf.write(headers_file_name)
    except Exception as e:
        console.print(f"[bold red]Error creating zip file: {e}[/bold red]")
        return
    finally:
        if os.path.exists(headers_file_name):
            os.remove(headers_file_name)

    console.print("Deploy zip created. Uploading to Netlify...")

    try:
        with open(zip_file_name, 'rb') as f:
            zip_data = f.read()
    except Exception as e:
        console.print(f"[bold red]Error reading zip file: {e}[/bold red]")
        return
    finally:
        if os.path.exists(zip_file_name):
            os.remove(zip_file_name)

    headers = {
        "Content-Type": "application/zip",
        "Authorization": f"Bearer {token}",
    }

    url = f"https://api.netlify.com/api/v1/sites/{site_id}/deploys"
    try:
        response = requests.post(url, headers=headers, data=zip_data,
                                 timeout=30)
        response.raise_for_status()
        console.print("[bold green]Deploy to Netlify successful![/bold green]")
    except requests.exceptions.RequestException as e:
        console.print("[bold red]--- Deploy FAILED ---[/bold red]")
        console.print(f"[red]Error: {e}[/red]")
        if e.response:
            console.print(f"[red]Response text: {e.response.text}[/red]")
