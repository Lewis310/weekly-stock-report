import yfinance as yf
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import os
from datetime import datetime, timedelta
import io
import json
import requests


# ── Gemini API ────────────────────────────────────────────────────────────────

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent"
)


def call_gemini(prompt: str) -> str:
    """Call Gemini 2.5 Flash (free tier) and return the response text."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY secret is not set.")

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1200},
    }
    resp = requests.post(
        f"{GEMINI_API_URL}?key={api_key}",
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Unexpected Gemini response: {data}") from exc


# ── Market Data ───────────────────────────────────────────────────────────────

TICKERS = {
    "SPY": "S&P 500",
    "QQQ": "NASDAQ 100",
    "DIA": "Dow Jones",
    "IWM": "Russell 2000",
}

SECTOR_ETFS = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLV": "Healthcare",
    "XLE": "Energy",
    "XLY": "Consumer Disc.",
}


def get_stock_data() -> dict:
    print("📊 Fetching index data…")
    end = datetime.now()
    start = end - timedelta(days=30)
    result = {}

    for ticker, name in TICKERS.items():
        try:
            hist = yf.Ticker(ticker).history(start=start, end=end)
            if len(hist) < 2:
                continue
            cur = hist["Close"].iloc[-1]
            prev = hist["Close"].iloc[-2]
            chg = cur - prev
            chg_pct = chg / prev * 100
            trend_5d = (
                (cur - hist["Close"].iloc[-5:].mean())
                / hist["Close"].iloc[-5:].mean()
                * 100
                if len(hist) >= 5
                else chg_pct
            )
            wk_high = hist["Close"].max()
            wk_low = hist["Close"].min()
            result[ticker] = {
                "name": name,
                "price": round(cur, 2),
                "change": round(chg, 2),
                "change_pct": round(chg_pct, 2),
                "trend_5d": round(trend_5d, 2),
                "volume": int(hist["Volume"].iloc[-1]),
                "high_30d": round(wk_high, 2),
                "low_30d": round(wk_low, 2),
            }
            print(f"  ✓ {name}: ${cur:.2f} ({chg_pct:+.2f}%)")
        except Exception as e:
            print(f"  ✗ {ticker}: {e}")

    return result


def get_sector_data() -> dict:
    print("📊 Fetching sector data…")
    end = datetime.now()
    start = end - timedelta(days=7)
    result = {}

    for ticker, name in SECTOR_ETFS.items():
        try:
            hist = yf.Ticker(ticker).history(start=start, end=end)
            if len(hist) < 2:
                continue
            cur = hist["Close"].iloc[-1]
            prev = hist["Close"].iloc[0]
            chg_pct = (cur - prev) / prev * 100
            result[ticker] = {"name": name, "change_pct": round(chg_pct, 2)}
        except Exception:
            pass

    return result


# ── AI Analysis ───────────────────────────────────────────────────────────────

def generate_analysis(stock_data: dict, sector_data: dict) -> dict:
    """Ask Gemini to produce a structured JSON market summary."""
    print("🤖 Generating AI analysis via Gemini…")

    index_lines = "\n".join(
        f"  {d['name']}: ${d['price']} ({d['change_pct']:+.2f}% today, "
        f"{d['trend_5d']:+.2f}% 5-day trend)"
        for d in stock_data.values()
    )
    sector_lines = "\n".join(
        f"  {d['name']}: {d['change_pct']:+.2f}% this week"
        for d in sector_data.values()
    )

    prompt = f"""You are a concise, professional market analyst writing a weekly briefing email.

Today is {datetime.now().strftime('%A, %d %B %Y')}.

## Index performance (daily)
{index_lines}

## Sector performance (this week)
{sector_lines}

Return ONLY valid JSON (no markdown fences) with this exact structure:
{{
  "headline": "One punchy 10-word sentence capturing the week's market mood",
  "sentiment": "Bullish | Neutral | Bearish",
  "sentiment_score": <integer 1-10, 1=very bearish, 10=very bullish>,
  "summary": "Two or three sentences of plain-English market overview.",
  "key_themes": [
    {{"theme": "Short theme title", "detail": "One sentence explanation."}},
    {{"theme": "Short theme title", "detail": "One sentence explanation."}},
    {{"theme": "Short theme title", "detail": "One sentence explanation."}}
  ],
  "sector_spotlight": "Name the strongest sector this week and explain why in one sentence.",
  "risk_watch": "One sentence on the biggest risk to monitor next week.",
  "actionable": "One concrete, specific thing an investor should consider this week."
}}"""

    raw = call_gemini(prompt)

    # Strip markdown fences
    raw = raw.strip()
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                raw = part
                break

    # Find the JSON object
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start == -1 or end == 0:
        raise RuntimeError(f"No JSON found in Gemini response: {raw}")
    raw = raw[start:end]

    return json.loads(raw)
# ── Chart ─────────────────────────────────────────────────────────────────────

def create_chart(stock_data: dict, sector_data: dict) -> io.BytesIO:
    print("📈 Creating chart…")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.patch.set_facecolor("#FAFAFA")

    # ── Left: index daily change ──────────────────────────────────────────────
    ax1 = axes[0]
    ax1.set_facecolor("#FFFFFF")
    names = [d["name"] for d in stock_data.values()]
    changes = [d["change_pct"] for d in stock_data.values()]
    colors = ["#16A34A" if c >= 0 else "#DC2626" for c in changes]

    bars = ax1.barh(names, changes, color=colors, height=0.55)
    ax1.axvline(0, color="#CBD5E1", linewidth=1)
    ax1.set_title("Daily Change (%)", fontsize=12, fontweight="bold",
                  color="#1E293B", pad=12)
    ax1.tick_params(labelsize=10, colors="#475569")
    ax1.spines[["top", "right", "left"]].set_visible(False)
    ax1.spines["bottom"].set_color("#E2E8F0")

    for bar, val in zip(bars, changes):
        x = bar.get_width()
        ax1.text(
            x + (0.05 if val >= 0 else -0.05),
            bar.get_y() + bar.get_height() / 2,
            f"{val:+.2f}%",
            va="center",
            ha="left" if val >= 0 else "right",
            fontsize=9,
            color="#1E293B",
            fontweight="bold",
        )

    # ── Right: sector weekly change ───────────────────────────────────────────
    ax2 = axes[1]
    ax2.set_facecolor("#FFFFFF")
    sec_names = [d["name"] for d in sector_data.values()]
    sec_changes = [d["change_pct"] for d in sector_data.values()]
    sec_colors = ["#16A34A" if c >= 0 else "#DC2626" for c in sec_changes]

    # Sort descending
    paired = sorted(zip(sec_changes, sec_names, sec_colors), reverse=True)
    sec_changes, sec_names, sec_colors = zip(*paired) if paired else ([], [], [])

    bars2 = ax2.barh(sec_names, sec_changes, color=sec_colors, height=0.55)
    ax2.axvline(0, color="#CBD5E1", linewidth=1)
    ax2.set_title("Sector Performance – Week (%)", fontsize=12, fontweight="bold",
                  color="#1E293B", pad=12)
    ax2.tick_params(labelsize=10, colors="#475569")
    ax2.spines[["top", "right", "left"]].set_visible(False)
    ax2.spines["bottom"].set_color("#E2E8F0")

    for bar, val in zip(bars2, sec_changes):
        x = bar.get_width()
        ax2.text(
            x + (0.05 if val >= 0 else -0.05),
            bar.get_y() + bar.get_height() / 2,
            f"{val:+.2f}%",
            va="center",
            ha="left" if val >= 0 else "right",
            fontsize=9,
            color="#1E293B",
            fontweight="bold",
        )

    plt.tight_layout(pad=2.5)
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120, bbox_inches="tight",
                facecolor="#FAFAFA")
    buf.seek(0)
    plt.close()
    return buf


# ── Email HTML ────────────────────────────────────────────────────────────────

def _sentiment_color(sentiment: str) -> str:
    return {"Bullish": "#16A34A", "Bearish": "#DC2626"}.get(sentiment, "#D97706")


def _sentiment_bg(sentiment: str) -> str:
    return {"Bullish": "#F0FDF4", "Bearish": "#FEF2F2"}.get(sentiment, "#FFFBEB")


def build_email_html(stock_data: dict, sector_data: dict, analysis: dict,
                     from_name: str) -> str:
    date_str = datetime.now().strftime("%A, %-d %B %Y")
    s_color = _sentiment_color(analysis["sentiment"])
    s_bg = _sentiment_bg(analysis["sentiment"])
    score = analysis.get("sentiment_score", 5)
    score_pct = int(score / 10 * 100)

    # ── Index rows ────────────────────────────────────────────────────────────
    index_rows = ""
    for ticker, d in stock_data.items():
        chg_color = "#16A34A" if d["change_pct"] >= 0 else "#DC2626"
        arrow = "▲" if d["change_pct"] >= 0 else "▼"
        trend_color = "#16A34A" if d["trend_5d"] >= 0 else "#DC2626"
        index_rows += f"""
        <tr>
          <td style="padding:12px 16px;border-bottom:1px solid #F1F5F9;font-weight:600;color:#1E293B;">{d['name']}</td>
          <td style="padding:12px 16px;border-bottom:1px solid #F1F5F9;font-family:monospace;color:#1E293B;">${d['price']:,.2f}</td>
          <td style="padding:12px 16px;border-bottom:1px solid #F1F5F9;color:{chg_color};font-weight:700;">{arrow} {d['change_pct']:+.2f}%</td>
          <td style="padding:12px 16px;border-bottom:1px solid #F1F5F9;color:{trend_color};font-size:13px;">{d['trend_5d']:+.2f}%</td>
          <td style="padding:12px 16px;border-bottom:1px solid #F1F5F9;font-size:12px;color:#94A3B8;">${d['low_30d']:,.0f} – ${d['high_30d']:,.0f}</td>
        </tr>"""

    # ── Sector bars ───────────────────────────────────────────────────────────
    sector_rows = ""
    max_abs = max((abs(d["change_pct"]) for d in sector_data.values()), default=1)
    for d in sorted(sector_data.values(), key=lambda x: x["change_pct"], reverse=True):
        bar_color = "#16A34A" if d["change_pct"] >= 0 else "#DC2626"
        bar_pct = int(abs(d["change_pct"]) / max_abs * 100)
        label_side = "left" if d["change_pct"] >= 0 else "right"
        sector_rows += f"""
        <tr>
          <td style="padding:8px 16px;width:130px;font-size:13px;color:#475569;white-space:nowrap;">{d['name']}</td>
          <td style="padding:8px 4px;">
            <div style="background:#F1F5F9;border-radius:3px;height:10px;overflow:hidden;">
              <div style="width:{bar_pct}%;background:{bar_color};height:100%;border-radius:3px;"></div>
            </div>
          </td>
          <td style="padding:8px 16px;width:60px;font-size:13px;font-weight:700;color:{bar_color};text-align:{label_side};">{d['change_pct']:+.2f}%</td>
        </tr>"""

    # ── Key themes ────────────────────────────────────────────────────────────
    themes_html = ""
    icons = ["◆", "◆", "◆"]
    for i, t in enumerate(analysis.get("key_themes", [])[:3]):
        themes_html += f"""
        <div style="margin-bottom:14px;padding:14px 16px;background:#F8FAFC;border-radius:8px;border-left:3px solid #3B82F6;">
          <div style="font-weight:700;color:#1E293B;margin-bottom:4px;">{icons[i]} {t['theme']}</div>
          <div style="font-size:14px;color:#64748B;line-height:1.5;">{t['detail']}</div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Weekly Market Report</title>
</head>
<body style="margin:0;padding:0;background:#F8FAFC;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;">

<!-- Wrapper -->
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F8FAFC;padding:32px 0;">
<tr><td align="center">
<table width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;">

  <!-- Header -->
  <tr>
    <td style="background:#FFFFFF;border-radius:12px 12px 0 0;padding:32px 40px 28px;border-bottom:1px solid #E2E8F0;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td>
            <div style="font-size:11px;font-weight:700;letter-spacing:2px;color:#94A3B8;text-transform:uppercase;margin-bottom:8px;">Weekly Market Report</div>
            <div style="font-size:26px;font-weight:800;color:#0F172A;line-height:1.2;">{analysis['headline']}</div>
          </td>
          <td valign="top" align="right" style="white-space:nowrap;padding-left:20px;">
            <div style="font-size:12px;color:#94A3B8;">{date_str}</div>
            <div style="margin-top:10px;display:inline-block;background:{s_bg};color:{s_color};font-weight:700;font-size:13px;padding:6px 14px;border-radius:20px;border:1.5px solid {s_color};">{analysis['sentiment']}</div>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- Summary -->
  <tr>
    <td style="background:#FFFFFF;padding:24px 40px;">
      <p style="margin:0;font-size:15px;color:#475569;line-height:1.7;">{analysis['summary']}</p>

      <!-- Sentiment meter -->
      <div style="margin-top:20px;">
        <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
          <span style="font-size:12px;font-weight:600;color:#94A3B8;text-transform:uppercase;letter-spacing:1px;">Market Mood</span>
          <span style="font-size:12px;font-weight:700;color:{s_color};">{score}/10</span>
        </div>
        <div style="background:#F1F5F9;border-radius:4px;height:6px;overflow:hidden;">
          <div style="width:{score_pct}%;background:linear-gradient(90deg,#EF4444,#EAB308,#22C55E);height:100%;border-radius:4px;"></div>
        </div>
        <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:4px;">
          <tr>
            <td style="font-size:11px;color:#CBD5E1;">Bearish</td>
            <td align="right" style="font-size:11px;color:#CBD5E1;">Bullish</td>
          </tr>
        </table>
      </div>
    </td>
  </tr>

  <!-- Divider -->
  <tr><td style="background:#FFFFFF;padding:0 40px;"><div style="height:1px;background:#F1F5F9;"></div></td></tr>

  <!-- Index Table -->
  <tr>
    <td style="background:#FFFFFF;padding:24px 40px 8px;">
      <div style="font-size:11px;font-weight:700;letter-spacing:2px;color:#94A3B8;text-transform:uppercase;margin-bottom:16px;">Major Indices</div>
      <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
        <thead>
          <tr style="background:#F8FAFC;">
            <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#94A3B8;letter-spacing:1px;text-transform:uppercase;">Index</th>
            <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#94A3B8;letter-spacing:1px;text-transform:uppercase;">Price</th>
            <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#94A3B8;letter-spacing:1px;text-transform:uppercase;">Today</th>
            <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#94A3B8;letter-spacing:1px;text-transform:uppercase;">5D Trend</th>
            <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#94A3B8;letter-spacing:1px;text-transform:uppercase;">30D Range</th>
          </tr>
        </thead>
        <tbody>{index_rows}</tbody>
      </table>
    </td>
  </tr>

  <!-- Chart image -->
  <tr>
    <td style="background:#FFFFFF;padding:8px 40px 28px;">
      <img src="cid:market_chart" width="560" style="width:100%;max-width:560px;border-radius:8px;border:1px solid #F1F5F9;" alt="Market chart">
    </td>
  </tr>

  <!-- Divider -->
  <tr><td style="background:#FFFFFF;padding:0 40px;"><div style="height:1px;background:#F1F5F9;"></div></td></tr>

  <!-- Sector heatmap -->
  <tr>
    <td style="background:#FFFFFF;padding:24px 40px 8px;">
      <div style="font-size:11px;font-weight:700;letter-spacing:2px;color:#94A3B8;text-transform:uppercase;margin-bottom:16px;">Sector Performance (Week)</div>
      <table width="100%" cellpadding="0" cellspacing="0">{sector_rows}</table>
    </td>
  </tr>

  <!-- Divider -->
  <tr><td style="background:#FFFFFF;padding:16px 40px 0;"><div style="height:1px;background:#F1F5F9;"></div></td></tr>

  <!-- Key themes -->
  <tr>
    <td style="background:#FFFFFF;padding:24px 40px 8px;">
      <div style="font-size:11px;font-weight:700;letter-spacing:2px;color:#94A3B8;text-transform:uppercase;margin-bottom:16px;">Key Themes</div>
      {themes_html}
    </td>
  </tr>

  <!-- Divider -->
  <tr><td style="background:#FFFFFF;padding:0 40px;"><div style="height:1px;background:#F1F5F9;"></div></td></tr>

  <!-- Callout cards -->
  <tr>
    <td style="background:#FFFFFF;padding:24px 40px 28px;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <!-- Sector spotlight -->
          <td width="49%" valign="top" style="background:#F0FDF4;border-radius:10px;padding:18px;">
            <div style="font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#16A34A;margin-bottom:8px;">Sector Spotlight</div>
            <div style="font-size:13px;color:#166534;line-height:1.6;">{analysis['sector_spotlight']}</div>
          </td>
          <td width="2%"></td>
          <!-- Risk watch -->
          <td width="49%" valign="top" style="background:#FEF2F2;border-radius:10px;padding:18px;">
            <div style="font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#DC2626;margin-bottom:8px;">Risk Watch</div>
            <div style="font-size:13px;color:#991B1B;line-height:1.6;">{analysis['risk_watch']}</div>
          </td>
        </tr>
      </table>

      <!-- Actionable -->
      <div style="margin-top:16px;background:#EFF6FF;border-radius:10px;padding:18px;">
        <div style="font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#2563EB;margin-bottom:8px;">This Week's Idea</div>
        <div style="font-size:14px;color:#1E40AF;line-height:1.6;font-weight:500;">{analysis['actionable']}</div>
      </div>
    </td>
  </tr>

  <!-- Footer -->
  <tr>
    <td style="background:#F8FAFC;border-radius:0 0 12px 12px;padding:20px 40px;border-top:1px solid #E2E8F0;">
      <p style="margin:0;font-size:12px;color:#94A3B8;text-align:center;line-height:1.6;">
        Prepared by {from_name} · {date_str}<br>
        <span style="font-size:11px;">Market data via Yahoo Finance · AI analysis via Google Gemini 2.5 Flash · For informational purposes only. Not financial advice.</span>
      </p>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""


# ── Send Email ────────────────────────────────────────────────────────────────

def send_email(html: str, chart: io.BytesIO, to_email: str, from_name: str) -> bool:
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    if not smtp_user or not smtp_pass:
        print("❌ SMTP credentials missing.")
        return False

    subject = f"📊 Weekly Market Report – {datetime.now().strftime('%-d %b %Y')}"

    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{smtp_user}>"
    msg["To"] = to_email

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(html, "html"))
    msg.attach(alt)

    img = MIMEImage(chart.getvalue(), _subtype="png")
    img.add_header("Content-ID", "<market_chart>")
    img.add_header("Content-Disposition", "inline", filename="market_chart.png")
    msg.attach(img)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)
        print("✅ Email sent!")
        return True
    except Exception as e:
        print(f"❌ Send failed: {e}")
        return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("🚀 Weekly Market Report starting…\n")

    required = ["EMAIL_TO", "FROM_NAME", "SMTP_USER", "SMTP_PASSWORD", "GEMINI_API_KEY"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        print(f"❌ Missing secrets: {', '.join(missing)}")
        return

    stock_data = get_stock_data()
    if not stock_data:
        print("❌ No stock data — aborting.")
        return

    sector_data = get_sector_data()
    analysis = generate_analysis(stock_data, sector_data)

    print(f"\n  Headline  : {analysis['headline']}")
    print(f"  Sentiment : {analysis['sentiment']} ({analysis['sentiment_score']}/10)\n")

    chart = create_chart(stock_data, sector_data)
    from_name = os.getenv("FROM_NAME", "Market Report")
    html = build_email_html(stock_data, sector_data, analysis, from_name)
    send_email(html, chart, os.getenv("EMAIL_TO"), from_name)


if __name__ == "__main__":
    main()
