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

def generate_clean_analysis(stock_data, political_news, industry_news):
    """Generate clean, organized market intelligence analysis"""
    print("🔄 Generating clean market analysis...")
    
    # Calculate market metrics
    up_count = sum(1 for data in stock_data.values() if data['change_pct'] > 0)
    down_count = sum(1 for data in stock_data.values() if data['change_pct'] < 0)
    avg_change = sum(data['change_pct'] for data in stock_data.values()) / len(stock_data)
    
    # Performance rankings
    performers = sorted(stock_data.values(), key=lambda x: x['change_pct'], reverse=True)
    best_performer = performers[0]
    worst_performer = performers[-1]
    
    # Market sentiment
    if avg_change > 1.0:
        sentiment = "strongly bullish"
    elif avg_change > 0.5:
        sentiment = "moderately bullish"
    elif avg_change > 0:
        sentiment = "slightly bullish"
    elif avg_change > -0.5:
        sentiment = "slightly bearish"
    else:
        sentiment = "bearish"

    analysis = f"""
**MARKET INTELLIGENCE SUMMARY**
*Generated {datetime.now().strftime('%m/%d/%Y %I:%M %p')}*

## 📈 MARKET OVERVIEW
- **Sentiment**: {sentiment.title()}
- **Performance**: {up_count} indices up, {down_count} down
- **Average Change**: {avg_change:+.2f}%
- **Leadership**: {best_performer['name']} (+{best_performer['change_pct']:+.2f}%)
- **Lagging**: {worst_performer['name']} ({worst_performer['change_pct']:+.2f}%)

## 🏛️ POLITICAL CATALYSTS

"""

    # Add political catalysts
    for i, news in enumerate(political_news, 1):
        analysis += f"""**{i}. {news['headline'].replace('Political Development: ', '')}**
   - Impact: {news['impact']}
   - Sectors: {', '.join(news['sectors_affected'])}
   - Urgency: {news['urgency']}

"""

    analysis += """## 🏭 SECTOR OUTLOOK

"""

    # Add sector outlook
    for i, news in enumerate(industry_news, 1):
        analysis += f"""**{i}. {news['industry']} Sector**
   - Development: {news['headline'].replace(f"{news['industry']} Update: ", "")}
   - Sentiment: {news['sentiment']}
   - Watch: {', '.join(news['stocks_to_watch'])}
   - Outlook: {news['impact']}

"""

    analysis += f"""## 💡 TRADING INSIGHTS

### Key Opportunities
- **{best_performer['name']} Momentum**: Leading with {best_performer['change_pct']:+.2f}% gain
- **Sector Focus**: {industry_news[0]['industry']} showing {industry_news[0]['sentiment'].lower()} momentum
- **Political Plays**: {political_news[0]['sectors_affected'][0]} sector affected by {political_news[0]['headline'].split(':')[1].strip()}

### Risk Considerations
- Monitor {worst_performer['name']} for potential reversal
- {political_news[0]['urgency']} urgency political development in {political_news[0]['sectors_affected'][0]}
- {industry_news[1]['industry']} sector showing {industry_news[1]['sentiment'].lower()} sentiment

### Actionable Items
1. Watch {best_performer['name']} for continued leadership
2. Monitor {political_news[0]['sectors_affected'][0]} for political impact
3. Track {industry_news[0]['stocks_to_watch'][0]} in {industry_news[0]['industry']} sector
4. Review {worst_performer['name']} for potential mean reversion

## 🎯 STRATEGIC OUTLOOK
The market shows {sentiment} characteristics with {industry_news[0]['industry']} leading and {political_news[0]['sectors_affected'][0]} facing political headwinds. Focus on quality names in strong sectors while managing exposure to politically sensitive areas.
"""

    return analysis

def create_email_html(stock_data, ai_analysis, political_news, industry_news, from_name):
    """Create visually appealing HTML email with consistent styling"""
    
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    
    # Create stock table rows
    stock_rows = ""
    for ticker, data in stock_data.items():
        change_color = "color: #2E8B57;" if data['change_pct'] >= 0 else "color: #DC143C;"
        trend_icon = "📈" if data['trend_5d'] > 0 else "📉" if data['trend_5d'] < 0 else "➡️"
        stock_rows += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #e0e0e0;">
                <strong>{data['name']}</strong>
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #e0e0e0;">
                ${data['current_price']:.2f}
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #e0e0e0; {change_color}">
                {data['change']:+.2f}
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #e0e0e0; {change_color}">
                {data['change_pct']:+.2f}%
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #e0e0e0; color: #666;">
                {trend_icon} {data['trend_5d']:+.1f}%
            </td>
        </tr>
        """
    
    # Create political news section with consistent styling
    political_html = ""
    for news in political_news:
        urgency_color = "#dc3545" if news['urgency'] == 'High' else "#ffc107" if news['urgency'] == 'Medium' else "#28a745"
        political_html += f"""
        <div style="margin: 12px 0; padding: 15px; background: white; border-radius: 8px; border-left: 4px solid {urgency_color}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="font-weight: bold; margin-bottom: 8px; color: #2c3e50; font-size: 15px;">{news['headline']}</div>
            <div style="color: #666; font-size: 14px; margin-bottom: 8px; line-height: 1.4;">{news['impact']}</div>
            <div style="font-size: 13px; color: #7f8c8d;">
                <span style="background: #f8f9fa; padding: 4px 8px; border-radius: 4px; margin-right: 8px;">
                    🎯 {', '.join(news['sectors_affected'])}
                </span>
                <span style="background: {urgency_color}15; color: {urgency_color}; padding: 4px 8px; border-radius: 4px;">
                    ⚡ {news['urgency']} Urgency
                </span>
            </div>
        </div>
        """
    
    # Create industry news section
    industry_html = ""
    for news in industry_news:
        sentiment_color = "#28a745" if news['sentiment'] == 'Positive' else "#dc3545" if news['sentiment'] == 'Negative' else "#6c757d"
        industry_html += f"""
        <div style="margin: 12px 0; padding: 15px; background: white; border-radius: 8px; border-left: 4px solid {sentiment_color}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="font-weight: bold; margin-bottom: 8px; color: #2c3e50; font-size: 15px;">
                🏭 {news['industry']}: {news['headline'].replace(f"{news['industry']} Update: ", "")}
            </div>
            <div style="color: #666; font-size: 14px; margin-bottom: 8px; line-height: 1.4;">{news['impact']}</div>
            <div style="font-size: 13px; color: #7f8c8d;">
                <span style="background: #f8f9fa; padding: 4px 8px; border-radius: 4px; margin-right: 8px;">
                    📊 {', '.join(news['stocks_to_watch'])}
                </span>
                <span style="background: {sentiment_color}15; color: {sentiment_color}; padding: 4px 8px; border-radius: 4px;">
                    📈 {news['sentiment']} Sentiment
                </span>
            </div>
        </div>
        """
    
    # Convert analysis to clean HTML with consistent styling
    analysis_lines = ai_analysis.split('\n')
    analysis_html = ""
    
    for line in analysis_lines:
        if line.startswith('**MARKET INTELLIGENCE SUMMARY**'):
            analysis_html += f'<div style="font-weight: bold; font-size: 16px; color: #2c3e50; margin-bottom: 8px;">{line.replace("**", "")}</div>'
        elif line.startswith('*Generated'):
            analysis_html += f'<div style="color: #6c757d; font-size: 13px; margin-bottom: 20px; font-style: italic;">{line}</div>'
        elif line.startswith('## '):
            analysis_html += f'<div style="font-weight: bold; font-size: 16px; color: #2c3e50; margin: 20px 0 12px 0; padding-bottom: 6px; border-bottom: 2px solid #667eea;">{line.replace("## ", "")}</div>'
        elif line.startswith('### '):
            analysis_html += f'<div style="font-weight: 600; font-size: 15px; color: #34495e; margin: 16px 0 10px 0;">{line.replace("### ", "")}</div>'
        elif line.startswith('- **') or line.startswith('**') and ':**' in line:
            # Handle bullet points and key-value lines
            clean_line = line.replace('**', '').replace('- ', '')
            if ':' in clean_line:
                parts = clean_line.split(':', 1)
                analysis_html += f'<div style="margin: 8px 0; line-height: 1.4;"><strong>{parts[0]}:</strong>{parts[1]}</div>'
            else:
                analysis_html += f'<div style="margin: 8px 0; line-height: 1.4;">• {clean_line}</div>'
        elif line.startswith('1. ') or line.startswith('2. ') or line.startswith('3. ') or line.startswith('4. '):
            analysis_html += f'<div style="margin: 8px 0 8px 15px; line-height: 1.4;">{line}</div>'
        elif line.strip() == '':
            analysis_html += '<div style="margin: 4px 0;"></div>'
        else:
            analysis_html += f'<div style="margin: 8px 0; line-height: 1.4; color: #666; font-size: 14px;">{line}</div>'
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 0; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; text-align: center; }}
        .content {{ padding: 25px; }}
        .section {{ margin-bottom: 30px; }}
        .stock-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .stock-table th {{ background-color: #f8f9fa; padding: 12px; text-align: left; font-weight: 600; color: #2c3e50; border-bottom: 2px solid #e9ecef; font-size: 14px; }}
        .stock-table td {{ padding: 12px; border-bottom: 1px solid #e9ecef; font-size: 14px; }}
        .analysis-box {{ background: white; padding: 25px; border-radius: 10px; line-height: 1.6; border: 1px solid #e9ecef; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .footer {{ text-align: center; padding: 25px; color: #6c757d; font-size: 13px; background: #f8f9fa; border-top: 1px solid #e9ecef; }}
        .section-title {{ color: #2c3e50; font-size: 18px; font-weight: 600; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #667eea; }}
        .news-section {{ background: #f8f9fa; border-radius: 10px; padding: 20px; margin: 20px 0; }}
        .news-title {{ color: #495057; font-size: 16px; font-weight: 600; margin-bottom: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0; font-size: 28px; font-weight: 300;">📊 Market Intelligence Report</h1>
            <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 16px;">{current_date}</p>
        </div>
        
        <div class="content">
            <div class="section">
                <h2 class="section-title">📈 Market Performance</h2>
                <table class="stock-table">
                    <tr>
                        <th>Index</th>
                        <th>Price</th>
                        <th>Change</th>
                        <th>% Change</th>
                        <th>5D Trend</th>
                    </tr>
                    {stock_rows}
                </table>
            </div>
            
            <div class="section">
                <h2 class="section-title">🏛️ Political Catalysts</h2>
                <div class="news-section">
                    {political_html}
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">🏭 Sector Outlook</h2>
                <div class="news-section">
                    {industry_html}
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">🤖 Integrated Market Intelligence</h2>
                <div class="analysis-box">
                    {analysis_html}
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>This report combines real-time market data with political and industry analysis for comprehensive insights.</p>
            <p>Prepared by: {from_name} • {current_date} • Data Sources: Market Data & Simulated Catalysts</p>
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
    msg['Subject'] = f"Market Intelligence Report - {datetime.now().strftime('%m/%d/%Y')}"
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
    print("🚀 Generating Clean Market Intelligence Report...")
    
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
    
    # Generate clean analysis
    ai_analysis = generate_clean_analysis(stock_data, political_news, industry_news)
    
    # Create email content
    from_name = os.getenv('FROM_NAME', 'Market Intelligence')
    html_content = create_email_html(stock_data, ai_analysis, political_news, industry_news, from_name)
    
    # Send email
    email_to = os.getenv('EMAIL_TO')
    success = send_email(html_content, chart_image, email_to, from_name)
    
    if success:
        print("🎉 Clean market intelligence report sent successfully!")
    else:
        print("💥 Failed to send market report")

if __name__ == "__main__":
    main()
