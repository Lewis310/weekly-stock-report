#!/usr/bin/env python3
"""
weekly_stock_report.py

Save this file and schedule it to run every Tuesday at 6:30am local time.
"""

import os
import io
import sys
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib
from typing import List

# ------------- Configuration ----------------
# Default indices and a sample watchlist (edit as you like)
INDICES = {
    "S&P 500": "^GSPC",
    "Nasdaq": "^IXIC",
    "Dow Jones": "^DJI",
    "VIX": "^VIX"
}

# Optional: your watchlist tickers (add / remove)
WATCHLIST = ["AAPL", "MSFT", "GOOGL", "AMZN"]

# Email / SMTP: use environment variables for credentials (see README below)
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER")    # your email
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")  # app password or SMTP password
EMAIL_FROM = os.environ.get("EMAIL_FROM", SMTP_USER)
EMAIL_TO = [addr.strip() for addr in os.environ.get("EMAIL_TO", "").split(",") if addr.strip()]
FROM_NAME = os.environ.get("FROM_NAME", "Weekly Market Report Bot")

# Reporting settings
DAYS_LOOKBACK = int(os.environ.get("DAYS_LOOKBACK", 7))  # 7 days is typical for weekly
PLOT_DPI = 150

# ------------- Helper functions ----------------

def fetch_close_series(ticker: str, period_days: int = 7) -> pd.Series:
    """Fetch daily close prices for the last period_days for ticker."""
    period_str = f"{period_days}d"
    try:
        df = yf.download(ticker, period=period_str, interval="1d", progress=False, threads=False)
    except Exception as e:
        print(f"yfinance download error for {ticker}: {e}", file=sys.stderr)
        raise
    if df.empty:
        return pd.Series(dtype=float)
    return df["Close"].dropna()

def pct_change(from_val: float, to_val: float) -> float:
    if from_val == 0:
        return 0.0
    return (to_val - from_val) / from_val * 100.0

def make_line_plot(series: pd.Series, title: str, filename: str):
    """Save a clean line chart of series to filename."""
    if series.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        fig.savefig(filename, dpi=PLOT_DPI, bbox_inches="tight")
        plt.close(fig)
        return

    fig, ax = plt.subplots(figsize=(8, 3.5), dpi=PLOT_DPI)
    ax.plot(series.index, series.values)
    ax.set_title(title, fontsize=12)
    ax.set_ylabel("Price")
    ax.grid(alpha=0.25)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(filename, bbox_inches="tight")
    plt.close(fig)

def compose_summary(index_results: List[dict], watch_results: List[dict]) -> str:
    """Create a human-readable paragraph summarising the movement."""
    parts = []
    # Indices summary
    idx_phrases = []
    for r in index_results:
        name = r["name"]
        ch = r["pct_change"]
        direction = "up" if ch > 0.2 else ("down" if ch < -0.2 else "flat")
        idx_phrases.append(f"{name} {direction} {ch:+.2f}%")
    parts.append("Indices: " + "; ".join(idx_phrases) + ".")

    # Highlight biggest mover in watchlist
    if watch_results:
        sorted_watch = sorted(watch_results, key=lambda x: abs(x["pct_change"]), reverse=True)
        top = sorted_watch[0]
        parts.append(f"Top mover in your watchlist: {top['ticker']} {top['pct_change']:+.2f}% over the week (from {top['start']:.2f} to {top['end']:.2f}).")

    # Simple overall sentiment
    avg_idx_change = sum([r["pct_change"] for r in index_results]) / max(1, len(index_results))
    sentiment = "modestly positive" if avg_idx_change > 0.2 else ("modestly negative" if avg_idx_change < -0.2 else "mixed/flat")
    parts.append(f"Overall weekly picture: {sentiment} (average index change {avg_idx_change:+.2f}%).")

    # Add a short recommendation/informational line
    parts.append("Note: this is a quick automated summary. For decisions, check full quotes, news and your risk plan.")

    return " ".join(parts)

def build_email_html(summary: str, image_cids: List[str]) -> str:
    """Construct HTML body referencing embedded images by CIDs."""
    # basic layout: header, summary paragraph, images inline
    images_html = "".join([f'<div style="margin-top:12px;"><img src="cid:{cid}" style="max-width:600px; width:100%; height:auto; border:1px solid #ddd;"/></div>' for cid in image_cids])
    now = datetime.now().strftime("%A, %B %d, %Y %I:%M %p")
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color:#111;">
        <h2 style="margin-bottom:4px;">Weekly US Market Report</h2>
        <small style="color:#666">{now}</small>
        <p style="font-size:14px; line-height:1.4;">{summary}</p>
        {images_html}
        <p style="color:#666; font-size:12px; margin-top:12px;">Generated automatically.</p>
      </body>
    </html>
    """
    return html

def send_email(subject: str, html_body: str, image_paths: List[str]):
    """Send email with inline images (CID) using SMTP."""
    if not SMTP_USER or not SMTP_PASSWORD:
        raise RuntimeError("SMTP_USER and SMTP_PASSWORD environment variables must be set.")

    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["From"] = f"{FROM_NAME} <{EMAIL_FROM}>"
    msg["To"] = ", ".join(EMAIL_TO)
    msg_alternative = MIMEMultipart("alternative")
    msg.attach(msg_alternative)

    msg_text = MIMEText("Please view this email in HTML-capable client.", "plain")
    msg_alternative.attach(msg_text)
    msg_html = MIMEText(html_body, "html")
    msg_alternative.attach(msg_html)

    # attach images with stable cids
    cids = []
    for idx, path in enumerate(image_paths):
        cid = f"img{idx}"
        cids.append(cid)
        try:
            with open(path, "rb") as f:
                img_data = f.read()
            mime = MIMEImage(img_data)
            mime.add_header("Content-ID", f"<{cid}>")
            mime.add_header("Content-Disposition", "inline", filename=os.path.basename(path))
            msg.attach(mime)
        except Exception as e:
            print(f"Warning: could not attach image {path}: {e}", file=sys.stderr)

    # send via SMTP
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=60)
    try:
        server.ehlo()
        if SMTP_PORT in (587, 25):
            server.starttls()
            server.ehlo()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        print("Email sent to:", EMAIL_TO)
    finally:
        server.quit()

# ------------- Main report generation ----------------

def main():
    if not EMAIL_TO:
        print("ERROR: Set EMAIL_TO environment variable (comma separated) to at least one recipient.", file=sys.stderr)
        return

    today = datetime.now().date()
    start_date = today - timedelta(days=DAYS_LOOKBACK)

    # fetch indices
    index_results = []
    image_paths = []

    for name, ticker in INDICES.items():
        series = fetch_close_series(ticker, period_days=DAYS_LOOKBACK)
        if series.empty:
            print(f"No data for {ticker} ({name})", file=sys.stderr)
            # still create a placeholder plot
        start_price = float(series.iloc[0]) if not series.empty else 0.0
        end_price = float(series.iloc[-1]) if not series.empty else 0.0
        ch = pct_change(start_price, end_price)
        index_results.append({"name": name, "ticker": ticker, "start": start_price, "end": end_price, "pct_change": ch})
        fname = f"/tmp/weekly_{ticker.replace('^','').replace('/','_')}.png"
        make_line_plot(series, f"{name} ({ticker}) — last {DAYS_LOOKBACK} days", fname)
        image_paths.append(fname)

    # fetch watchlist
    watch_results = []
    if WATCHLIST:
        # aggregate watchlist into one chart (multiple lines)
        df_watch = pd.DataFrame()
        for t in WATCHLIST:
            s = fetch_close_series(t, period_days=DAYS_LOOKBACK)
            if s.empty:
                continue
            df_watch[t] = s
            watch_results.append({"ticker": t, "start": float(s.iloc[0]), "end": float(s.iloc[-1]), "pct_change": pct_change(float(s.iloc[0]), float(s.iloc[-1]))})
        # plot watchlist multi-line
        if not df_watch.empty:
            fname_watch = "/tmp/watchlist_weekly.png"
            fig, ax = plt.subplots(figsize=(9,4), dpi=PLOT_DPI)
            df_watch.plot(ax=ax, legend=True)
            ax.set_title("Watchlist — last {} days".format(DAYS_LOOKBACK))
            ax.set_ylabel("Price")
            ax.grid(alpha=0.2)
            fig.autofmt_xdate()
            fig.tight_layout()
            fig.savefig(fname_watch, bbox_inches="tight")
            plt.close(fig)
            image_paths.append(fname_watch)

    # compose summary and html
    summary = compose_summary(index_results, watch_results)
    html_body = build_email_html(summary, [f"img{i}" for i in range(len(image_paths))])

    # send email
    subject = f"Weekly US Market Report — {datetime.now().strftime('%Y-%m-%d')}"
    send_email(subject, html_body, image_paths)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("Report generation failed:", exc, file=sys.stderr)
        raise
