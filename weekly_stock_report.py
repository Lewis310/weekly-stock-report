import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import os
from datetime import datetime, timedelta
import io
import random
import requests
from bs4 import BeautifulSoup

def get_stock_data():
    """Fetch major US stock indices data"""
    print("📊 Fetching stock data...")
    tickers = {
        'SPY': 'S&P 500',
        'QQQ': 'NASDAQ 100', 
        'DIA': 'Dow Jones',
        'IWM': 'Russell 2000'
    }
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    stock_data = {}
    
    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)
            
            if len(hist) > 1:
                current_price = hist['Close'][-1]
                prev_close = hist['Close'][-2]
                change = current_price - prev_close
                change_pct = (change / prev_close) * 100
                
                # Calculate 5-day trend
                if len(hist) >= 5:
                    five_day_avg = hist['Close'][-5:].mean()
                    trend_5d = ((current_price - five_day_avg) / five_day_avg) * 100
                else:
                    trend_5d = change_pct
                
                stock_data[ticker] = {
                    'name': name,
                    'current_price': round(current_price, 2),
                    'change': round(change, 2),
                    'change_pct': round(change_pct, 2),
                    'volume': hist['Volume'][-1],
                    'trend_5d': round(trend_5d, 2)
                }
                print(f"✅ {name}: ${current_price:.2f} ({change_pct:+.2f}%)")
        except Exception as e:
            print(f"❌ Error fetching data for {ticker}: {e}")
    
    return stock_data

def get_political_news():
    """Generate simulated political news that could impact markets"""
    print("🏛️ Generating political news context...")
    
    political_topics = [
        "Federal Reserve policy outlook and interest rate decisions",
        "Congressional budget negotiations and government funding",
        "Geopolitical tensions and international trade relations",
        "Regulatory changes affecting key industries",
        "Election developments and political polling data",
        "Fiscal policy and stimulus package discussions",
        "International diplomacy and trade agreements",
        "Environmental and climate policy initiatives",
        "Tax policy reforms and corporate tax rates",
        "Healthcare policy and pharmaceutical regulations"
    ]
    
    market_impacts = [
        "could create volatility in bond markets",
        "may affect technology sector sentiment",
        "likely to influence energy prices",
        "could impact international trade flows",
        "may affect consumer confidence indicators",
        "likely to influence infrastructure spending",
        "could create regulatory uncertainty",
        "may affect defense and aerospace sectors",
        "likely to impact renewable energy stocks",
        "could influence banking sector performance"
    ]
    
    news_items = []
    for i in range(3):  # Generate 3 political news items
        topic = random.choice(political_topics)
        impact = random.choice(market_impacts)
        urgency = random.choice(["immediate", "near-term", "medium-term"])
        
        news_item = {
            'headline': f"Political Development: {topic}",
            'impact': f"This development {impact} and requires monitoring for {urgency} market effects.",
            'sectors_affected': random.sample(['Technology', 'Financials', 'Energy', 'Healthcare', 'Industrials'], 2),
            'urgency': random.choice(['High', 'Medium', 'Low'])
        }
        news_items.append(news_item)
    
    return news_items

def get_industry_news():
    """Generate simulated industry-specific news"""
    print("🏭 Generating industry news context...")
    
    industries = {
        'Technology': [
            "Semiconductor export restrictions and supply chain developments",
            "AI regulation and technology innovation policies",
            "Big tech antitrust investigations and legal proceedings",
            "Cybersecurity threats and digital infrastructure spending",
            "5G deployment and telecommunications infrastructure"
        ],
        'Financials': [
            "Banking sector stress tests and capital requirements",
            "Interest rate sensitivity and net interest margin analysis",
            "Financial regulation and compliance developments",
            "M&A activity in banking and insurance sectors",
            "Fintech disruption and digital banking trends"
        ],
        'Healthcare': [
            "FDA drug approval pipeline and clinical trial results",
            "Healthcare policy reforms and Medicare/Medicaid changes",
            "Biotechnology innovation and pharmaceutical R&D",
            "Medical device regulation and innovation",
            "Healthcare services and hospital operator developments"
        ],
        'Energy': [
            "OPEC+ production decisions and oil price dynamics",
            "Renewable energy adoption and clean technology investments",
            "Energy infrastructure and pipeline developments",
            "Electric vehicle adoption and battery technology",
            "Natural gas supply and demand dynamics"
        ],
        'Consumer': [
            "Retail sales data and consumer spending trends",
            "E-commerce growth and digital transformation",
            "Supply chain disruptions and inventory levels",
            "Consumer confidence and discretionary spending",
            "Brand performance and market share dynamics"
        ]
    }
    
    industry_news = []
    selected_industries = random.sample(list(industries.keys()), 3)
    
    for industry in selected_industries:
        topic = random.choice(industries[industry])
        impact_level = random.choice(['Significant', 'Moderate', 'Limited'])
        time_frame = random.choice(['immediate', 'quarterly', 'annual'])
        
        news_item = {
            'industry': industry,
            'headline': f"{industry} Update: {topic}",
            'impact': f"{impact_level} impact expected with {time_frame} implications for sector performance.",
            'stocks_to_watch': get_representative_stocks(industry),
            'sentiment': random.choice(['Positive', 'Neutral', 'Negative'])
        }
        industry_news.append(news_item)
    
    return industry_news

def get_representative_stocks(industry):
    """Get representative stocks for each industry"""
    industry_stocks = {
        'Technology': ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'ADBE'],
        'Financials': ['JPM', 'BAC', 'GS', 'MS', 'V'],
        'Healthcare': ['JNJ', 'PFE', 'UNH', 'LLY', 'ABT'],
        'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG'],
        'Consumer': ['AMZN', 'WMT', 'TSLA', 'NKE', 'MCD']
    }
    return random.sample(industry_stocks.get(industry, ['SPY']), 2)

def create_stock_chart(stock_data):
    """Create a visualization of stock performance"""
    print("📈 Creating market chart...")
    plt.style.use('seaborn-v0_8')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Price chart
    names = [data['name'] for data in stock_data.values()]
    prices = [data['current_price'] for data in stock_data.values()]
    colors = ['#2E8B57' if data['change_pct'] >= 0 else '#DC143C' for data in stock_data.values()]
    
    bars = ax1.bar(names, prices, color=colors, alpha=0.7)
    ax1.set_title('Current Prices of Major Indices', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Price ($)')
    ax1.tick_params(axis='x', rotation=45)
    
    # Add value labels on bars
    for bar, price in zip(bars, prices):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(prices)*0.01,
                f'${price}', ha='center', va='bottom', fontweight='bold')
    
    # Percentage change chart
    changes = [data['change_pct'] for data in stock_data.values()]
    colors_change = ['green' if change >= 0 else 'red' for change in changes]
    
    bars2 = ax2.bar(names, changes, color=colors_change, alpha=0.7)
    ax2.set_title('Daily Percentage Change', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Change (%)')
    ax2.tick_params(axis='x', rotation=45)
    
    # Add percentage labels on bars
    for bar, change in zip(bars2, changes):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (0.1 if change >= 0 else -0.5),
                f'{change:+.2f}%', ha='center', va='bottom' if change >= 0 else 'top', 
                fontweight='bold', color='black')
    
    plt.tight_layout()
    
    # Save chart to bytes
    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='png', dpi=100, bbox_inches='tight')
    img_bytes.seek(0)
    plt.close()
    
    return img_bytes

def generate_enhanced_analysis(stock_data, political_news, industry_news):
    """Generate comprehensive analysis including political and industry context"""
    print("🔄 Generating comprehensive market analysis...")
    
    # Calculate comprehensive market metrics
    up_count = sum(1 for data in stock_data.values() if data['change_pct'] > 0)
    down_count = sum(1 for data in stock_data.values() if data['change_pct'] < 0)
    avg_change = sum(data['change_pct'] for data in stock_data.values()) / len(stock_data)
    total_volume = sum(data['volume'] for data in stock_data.values())
    avg_volume = total_volume / len(stock_data)
    
    # Performance rankings
    performers = sorted(stock_data.values(), key=lambda x: x['change_pct'], reverse=True)
    best_performer = performers[0]
    worst_performer = performers[-1]
    
    # Trend analysis
    positive_trends = sum(1 for data in stock_data.values() if data['trend_5d'] > 0)
    trend_strength = sum(data['trend_5d'] for data in stock_data.values()) / len(stock_data)
    
    # Market sentiment classification
    if avg_change > 1.0:
        sentiment = "strongly bullish"
        intensity = "high momentum"
    elif avg_change > 0.5:
        sentiment = "moderately bullish" 
        intensity = "steady momentum"
    elif avg_change > 0:
        sentiment = "slightly bullish"
        intensity = "cautious optimism"
    elif avg_change > -0.5:
        sentiment = "slightly bearish"
        intensity = "mild pressure"
    elif avg_change > -1.0:
        sentiment = "moderately bearish"
        intensity = "notable selling pressure"
    else:
        sentiment = "strongly bearish"
        intensity = "significant downturn"
    
    # Generate political context summary
    political_summary = " | ".join([news['headline'].replace('Political Development: ', '') for news in political_news[:2]])
    
    # Generate industry context summary
    industry_summary = " | ".join([f"{news['industry']}: {news['sentiment']}" for news in industry_news[:2]])
    
    analysis = f"""
    **COMPREHENSIVE MARKET INTELLIGENCE REPORT**
    **As of {datetime.now().strftime('%A, %B %d, %Y %I:%M %p')}**

    **EXECUTIVE SUMMARY:**
    The US equity markets are currently exhibiting {sentiment} characteristics with {intensity}. The overall market landscape shows {up_count} major indices advancing and {down_count} declining, with average performance at {avg_change:+.2f}%. Today's trading occurs against a backdrop of political developments including {political_summary} and industry dynamics showing {industry_summary}.

    **POLITICAL AND POLICY CONTEXT:**
    """

    # Add political news analysis
    for i, news in enumerate(political_news, 1):
        analysis += f"""
    {i}. **{news['headline']}** - {news['impact']} This primarily affects {', '.join(news['sectors_affected'])} sectors. Urgency level: {news['urgency']}.
        """

    analysis += """
    **INDUSTRY-SPECIFIC DEVELOPMENTS:**
    """

    # Add industry news analysis
    for i, news in enumerate(industry_news, 1):
        analysis += f"""
    {i}. **{news['industry']} Sector:** {news['headline']} - {news['impact']} Key stocks to watch: {', '.join(news['stocks_to_watch'])}. Sector sentiment: {news['sentiment']}.
        """

    analysis += f"""
    **DETAILED MARKET PERFORMANCE ANALYSIS:**

    **Leadership Analysis:**
    • **Top Performer:** {best_performer['name']} demonstrated exceptional strength with a gain of {best_performer['change_pct']:+.2f}%, establishing clear leadership.
    • **Lagging Performance:** {worst_performer['name']} underperformed with a decline of {worst_performer['change_pct']:+.2f}%.

    **Market Breadth and Participation:**
    Market breadth measures at {(up_count/(up_count+down_count))*100:.1f}%, indicating {'broad participation' if up_count > down_count else 'selective buying'}. The advance-decline ratio of {up_count}:{down_count} provides context for today's trading dynamics.

    **Volume and Liquidity Analysis:**
    Total trading volume across major indices reached approximately {total_volume:,.0f} shares, suggesting {'strong institutional participation' if avg_volume > 5000000 else 'moderate trading activity'}.

    **INTEGRATED MARKET OUTLOOK:**

    **Political Impact Assessment:**
    The current political environment suggests {random.choice(['increased regulatory scrutiny', 'policy stability', 'fiscal support measures', 'trade policy uncertainties'])} that may influence market direction. Key political factors to monitor include {political_news[0]['headline'].replace('Political Development: ', '')} and {political_news[1]['headline'].replace('Political Development: ', '')}.

    **Industry Rotation Implications:**
    Sector-level developments indicate {industry_news[0]['industry']} showing {industry_news[0]['sentiment'].lower()} momentum while {industry_news[1]['industry']} exhibits {industry_news[1]['sentiment'].lower()} characteristics. This rotation pattern suggests {'defensive positioning' if 'Healthcare' in [news['industry'] for news in industry_news] and industry_news[[news['industry'] for news in industry_news].index('Healthcare')]['sentiment'] == 'Positive' else 'growth-oriented exposure'}.

    **TRADING IMPLICATIONS AND STRATEGIC POSITIONING:**

    **Near-Term Directional Bias (Next 1-2 Sessions):**
    Given the {sentiment} market environment combined with current political and industry dynamics, traders should monitor for:
    • Political developments affecting {political_news[0]['sectors_affected'][0]} and {political_news[0]['sectors_affected'][1]} sectors
    • Industry-specific news in {industry_news[0]['industry']} and {industry_news[1]['industry']}
    • Technical levels in {best_performer['name']} as leadership indicator

    **Risk Management Considerations:**
    Position sizing should account for potential volatility from:
    • Political event risk: {political_news[0]['urgency']} urgency
    • Sector rotation: {industry_news[0]['industry']} vs {industry_news[1]['industry']} divergence
    • Market technicals: {trend_strength:+.2f}% 5-day trend strength

    **CRITICAL MONITORING FACTORS:**

    1. **Political Developments:** {political_news[0]['headline']}
    2. **Industry Leadership:** {industry_news[0]['industry']} sector momentum
    3. **Market Breadth:** Sustainability of {(up_count/(up_count+down_count))*100:.1f}% advance rate
    4. **Volume Confirmation:** Institutional participation levels

    **CONCLUSION:**
    The current market environment presents a {sentiment} backdrop influenced by political developments and sector rotation. Strategic positioning should emphasize selective exposure to {industry_news[0]['industry']} and {industry_news[1]['industry']} while monitoring political developments in {political_news[0]['sectors_affected'][0]}. The combination of {best_performer['name']} leadership and {political_summary.split('|')[0].strip()} creates a complex but opportunity-rich trading environment.
    """

    return analysis

def create_email_html(stock_data, ai_analysis, political_news, industry_news, from_name):
    """Create visually appealing HTML email with news sections"""
    
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    
    # Create stock table rows
    stock_rows = ""
    for ticker, data in stock_data.items():
        change_color = "color: #2E8B57;" if data['change_pct'] >= 0 else "color: #DC143C;"
        stock_rows += f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>{data['name']}</strong></td>
            <td style="padding: 8px; border-bottom: 1px solid #ddd;">${data['current_price']:.2f}</td>
            <td style="padding: 8px; border-bottom: 1px solid #ddd; {change_color}">{data['change']:+.2f}</td>
            <td style="padding: 8px; border-bottom: 1px solid #ddd; {change_color}">{data['change_pct']:+.2f}%</td>
        </tr>
        """
    
    # Create political news section
    political_html = ""
    for news in political_news:
        urgency_color = "#dc3545" if news['urgency'] == 'High' else "#ffc107" if news['urgency'] == 'Medium' else "#28a745"
        political_html += f"""
        <div style="margin-bottom: 15px; padding: 12px; background: #f8f9fa; border-radius: 5px; border-left: 4px solid {urgency_color};">
            <strong>{news['headline']}</strong><br>
            <span style="color: #666; font-size: 14px;">{news['impact']}</span><br>
            <small><strong>Sectors affected:</strong> {', '.join(news['sectors_affected'])} | 
            <strong>Urgency:</strong> <span style="color: {urgency_color}">{news['urgency']}</span></small>
        </div>
        """
    
    # Create industry news section
    industry_html = ""
    for news in industry_news:
        sentiment_color = "#28a745" if news['sentiment'] == 'Positive' else "#dc3545" if news['sentiment'] == 'Negative' else "#6c757d"
        industry_html += f"""
        <div style="margin-bottom: 15px; padding: 12px; background: #f8f9fa; border-radius: 5px; border-left: 4px solid {sentiment_color};">
            <strong>{news['headline']}</strong><br>
            <span style="color: #666; font-size: 14px;">{news['impact']}</span><br>
            <small><strong>Stocks to watch:</strong> {', '.join(news['stocks_to_watch'])} | 
            <strong>Sentiment:</strong> <span style="color: {sentiment_color}">{news['sentiment']}</span></small>
        </div>
        """
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}
        .container {{ max-width: 750px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
        .content {{ padding: 20px; }}
        .section {{ margin-bottom: 25px; }}
        .stock-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        .stock-table th {{ background-color: #f8f9fa; padding: 10px; text-align: left; }}
        .analysis-box {{ background: #f8f9fa; padding: 20px; border-left: 4px solid #667eea; border-radius: 5px; line-height: 1.6; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        .news-section {{ background: #fff; border: 1px solid #e9ecef; border-radius: 8px; padding: 15px; margin: 15px 0; }}
        .section-title {{ color: #2c3e50; border-bottom: 2px solid #667eea; padding-bottom: 8px; }}
        .news-title {{ color: #495057; font-size: 18px; margin-bottom: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 Market Intelligence & News Report</h1>
            <p>{current_date} | Political & Industry Insights</p>
        </div>
        
        <div class="content">
            <div class="section">
                <h2 class="section-title">Market Performance Snapshot</h2>
                <table class="stock-table">
                    <tr>
                        <th>Index</th>
                        <th>Price</th>
                        <th>Change</th>
                        <th>% Change</th>
                    </tr>
                    {stock_rows}
                </table>
            </div>
            
            <div class="section">
                <h2 class="section-title">🏛️ Political & Policy Developments</h2>
                <div class="news-section">
                    <div class="news-title">Key Political Factors Impacting Markets</div>
                    {political_html}
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">🏭 Industry & Sector Developments</h2>
                <div class="news-section">
                    <div class="news-title">Sector-Specific News and Analysis</div>
                    {industry_html}
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">📊 Market Visualization</h2>
                <p><em>Detailed performance charts attached for visual analysis</em></p>
            </div>
            
            <div class="section">
                <h2 class="section-title">🤖 Integrated Market Intelligence</h2>
                <div class="analysis-box">
                    {ai_analysis.replace(chr(10), '<br>')}
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Comprehensive market intelligence report with political and industry context • Data sources: Simulated market-moving events</p>
            <p>Prepared by: {from_name} • {current_date}</p>
            <p><em>This analysis integrates political, industry, and market factors for comprehensive insights.</em></p>
        </div>
    </div>
</body>
</html>
    """
    
    return html_content

def send_email(html_content, chart_image, to_email, from_name):
    """Send email with HTML content and chart attachment"""
    
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    if not smtp_user or not smtp_password:
        print("❌ SMTP credentials not found. Please check your GitHub Secrets.")
        return False
    
    msg = MIMEMultipart()
    msg['Subject'] = f"Market Intelligence with Political & Industry News - {datetime.now().strftime('%m/%d/%Y')}"
    msg['From'] = f"{from_name} <{smtp_user}>"
    msg['To'] = to_email
    
    # Attach HTML content
    msg.attach(MIMEText(html_content, 'html'))
    
    # Attach chart image
    chart_attachment = MIMEImage(chart_image.getvalue())
    chart_attachment.add_header('Content-Disposition', 'attachment', filename='market_chart.png')
    msg.attach(chart_attachment)
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        print("✅ Email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        return False

def main():
    """Main function to generate and send the market report"""
    print("🚀 Generating Comprehensive Market Intelligence Report...")
    
    # Validate environment variables
    required_vars = ['EMAIL_TO', 'FROM_NAME', 'SMTP_USER', 'SMTP_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your GitHub Secrets configuration.")
        return
    
    print("✅ All environment variables found!")
    
    # Fetch stock data
    stock_data = get_stock_data()
    
    if not stock_data:
        print("❌ No stock data retrieved. Check your internet connection.")
        return
    
    # Get political and industry news
    political_news = get_political_news()
    industry_news = get_industry_news()
    
    # Create visualization
    chart_image = create_stock_chart(stock_data)
    
    # Generate comprehensive analysis including news context
    ai_analysis = generate_enhanced_analysis(stock_data, political_news, industry_news)
    
    # Create email content
    from_name = os.getenv('FROM_NAME', 'Market Intelligence System')
    html_content = create_email_html(stock_data, ai_analysis, political_news, industry_news, from_name)
    
    # Send email
    email_to = os.getenv('EMAIL_TO')
    success = send_email(html_content, chart_image, email_to, from_name)
    
    if success:
        print("🎉 Comprehensive market intelligence report with news context sent successfully!")
    else:
        print("💥 Failed to send market report")

if __name__ == "__main__":
    main()
