import os
from datetime import date
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import openai
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib

# -------------------------
# 1️⃣ Fetch stock market data
# -------------------------
TICKERS = ["^GSPC", "^DJI", "^IXIC"]  # S&P 500, Dow Jones, NASDAQ
data = {}
for ticker in TICKERS:
    df = yf.download(ticker, period="7d", interval="1d", auto_adjust=True)  # auto_adjust fixes warning
    df.reset_index(inplace=True)
    data[ticker] = df

# Create simple summary for AI
market_summary = ""
for ticker, df in data.items():
    start_price = df['Close'].values[0]   # use .values[0] to get a float
    end_price = df['Close'].values[-1]    # last value as float
    change = end_price - start_price
    pct_change = (change / start_price) * 100
    market_summary += f"{ticker}: {start_price:.2f} -> {end_price:.2f} ({pct_change:.2f}%)\n"

# -------------------------
# 2️⃣ Generate AI Analysis
# -------------------------
openai.api_key = os.environ.get("OPENAI_API_KEY")

def generate_ai_summary(summary_text):
    prompt = f"""
    You are a professional financial analyst. Using the following market summary:
    {summary_text}
    Write a 3-4 paragraph weekly US stock market report suitable for an email.
    Include insights, trends, and key points for investors.
    """
    response = openai.ChatCompletion.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=600
    )
    return response['choices'][0]['message']['content']

ai_paragraph = generate_ai_summary(market_summary)

# -------------------------
# 3️⃣ Create chart
# -------------------------
plt.figure(figsize=(10,5))
for ticker, df in data.items():
    plt.plot(df['Date'], df['Close'], label=ticker)
plt.title("Weekly US Market Index Movement")
plt.xlabel("Date")
plt.ylabel("Closing Price")
plt.legend()
plt.grid(True)

# Save chart
os.makedirs("reports", exist_ok=True)
today = date.today().isoformat()
graph_path = f"reports/{today}-market.png"
plt.savefig(graph_path, bbox_inches="tight")
plt.close()

# -------------------------
# 4️⃣ Save Markdown report
# -------------------------
md_path = f"reports/{today}-report.md"
with open(md_path, "w", encoding="utf-8") as f:
    f.write(f"# Weekly US Market Report ({today})\n\n")
    f.write(f"{ai_paragraph}\n\n")
    f.write(f"![Market Graph](./{today}-market.png)\n")

print(f"Markdown report saved at: {md_path}")

# -------------------------
# 5️⃣ Create HTML email
# -------------------------
html_body = f"""
<div style="font-family:Arial, sans-serif; line-height:1.5; color:#333;">
    <h1 style="color:#1a73e8;">Weekly US Market Report</h1>
    <p style="font-size:14px;">{ai_paragraph}</p>
    <div style="text-align:center; margin:20px 0;">
        <img src="cid:market_graph" alt="Market Graph" style="width:600px; border:1px solid #ccc; padding:5px; border-radius:8px;">
    </div>
    <p style="font-size:12px; color:#777;">Generated automatically by your Weekly Market Bot.</p>
</div>
"""

# -------------------------
# 6️⃣ Send Email
# -------------------------
msg = MIMEMultipart()
msg['From'] = f"{os.environ.get('FROM_NAME')} <{os.environ.get('SMTP_USER')}>"
msg['To'] = os.environ.get('EMAIL_TO')
msg['Subject'] = f"US Market Weekly Report - {today}"

msg.attach(MIMEText(html_body, 'html'))

with open(graph_path, 'rb') as f:
    img = MIMEImage(f.read())
    img.add_header('Content-ID', '<market_graph>')
    img.add_header('Content-Disposition', 'inline', filename='market_graph.png')
    msg.attach(img)

with smtplib.SMTP('smtp.gmail.com', 587) as server:
    server.starttls()
    server.login(os.environ.get('SMTP_USER'), os.environ.get('SMTP_PASSWORD'))
    server.send_message(msg)

print(f"Email sent to: {os.environ.get('EMAIL_TO')}")
