import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import openai
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import os
from datetime import datetime, timedelta
import io

def get_stock_data():
    """Fetch major US stock indices data"""
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
                
                stock_data[ticker] = {
                    'name': name,
                    'current_price': round(current_price, 2),
                    'change': round(change, 2),
                    'change_pct': round(change_pct, 2),
                    'volume': hist['Volume'][-1]
                }
                print(f"✅ {name}: ${current_price:.2f} ({change_pct:+.2f}%)")
        except Exception as e:
            print(f"❌ Error fetching data for {ticker}: {e}")
    
    return stock_data

def create_stock_chart(stock_data):
    """Create a visualization of stock performance"""
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

def generate_ai_analysis(stock_data):
    """Generate AI analysis using OpenAI"""
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        return "❌ OpenAI API key not found. Please check your GitHub Secrets."
    
    openai.api_key = openai_api_key
    
    # Create prompt with stock data
    stock_summary = "\n".join([
        f"{data['name']}: ${data['current_price']} ({data['change_pct']:+.2f}%)"
        for data in stock_data.values()
    ])
    
    prompt = f"""
    As a financial analyst, provide a concise but insightful market summary based on the following US stock market data:

    {stock_summary}

    Please provide:
    1. A brief overall market summary (2-3 sentences)
    2. Key observations about today's movement
    3. Short-term outlook (next 1-2 days)
    4. One key factor to watch

    Keep it professional, data-driven, and avoid hype. Use clear, concise language suitable for a morning email report.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional financial analyst providing morning market insights."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ AI Analysis temporarily unavailable. Using fallback analysis.\n\nMarket Summary:\n{stock_summary}"

def create_email_html(stock_data, ai_analysis, from_name):
    """Create visually appealing HTML email"""
    
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    
    # Create stock table rows - FIXED: No backslashes in f-strings
    stock_rows = ""
    for ticker, data in stock_data.items():
        change_color = "color: #2E8B57;" if data['change_pct'] >= 0 else "color: #DC143C;"
        stock_row = f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>{data['name']}</strong></td>
            <td style="padding: 8px; border-bottom: 1px solid #ddd;">${data['current_price']:.2f}</td>
            <td style="padding: 8px; border-bottom: 1px solid #ddd; {change_color}">{data['change']:+.2f}</td>
            <td style="padding: 8px; border-bottom: 1px solid #ddd; {change_color}">{data['change_pct']:+.2f}%</td>
        </tr>
        """
        stock_rows += stock_row
    
    # FIXED: Use triple quotes without backslashes in f-strings
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
        .content {{ padding: 20px; }}
        .section {{ margin-bottom: 20px; }}
        .stock-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        .stock-table th {{ background-color: #f8f9fa; padding: 10px; text-align: left; }}
        .analysis-box {{ background: #f8f9fa; padding: 15px; border-left: 4px solid #667eea; border-radius: 5px; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 Morning Market Report</h1>
            <p>{current_date}</p>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>Market Snapshot</h2>
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
                <h2>📊 Market Visualization</h2>
                <p><em>See attached chart for detailed performance visualization</em></p>
            </div>
            
            <div class="section">
                <h2>🤖 AI Market Analysis</h2>
                <div class="analysis-box">
                    {ai_analysis.replace(chr(10), '<br>')}
                </div>
            </div>
            
            <div class="section">
                <h3>Key Takeaways</h3>
                <ul>
                    <li>Real-time data as of market open</li>
                    <li>AI-powered insights and predictions</li>
                    <li>Visual performance tracking</li>
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <p>This report was generated automatically by AI • Data source: Yahoo Finance</p>
            <p>Prepared by: {from_name} • {current_date}</p>
            <p><em>This is for informational purposes only. Invest at your own risk.</em></p>
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
    msg['Subject'] = f"Morning Stock Market Report - {datetime.now().strftime('%m/%d/%Y')}"
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
    print("🚀 Generating Morning Market Report...")
    
    # Validate environment variables
    required_vars = ['EMAIL_TO', 'FROM_NAME', 'OPENAI_API_KEY', 'SMTP_USER', 'SMTP_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your GitHub Secrets configuration.")
        return
    
    print("✅ All environment variables found!")
    
    # Fetch stock data
    print("📊 Fetching stock data...")
    stock_data = get_stock_data()
    
    if not stock_data:
        print("❌ No stock data retrieved. Check your internet connection.")
        return
    
    # Create visualization
    print("📈 Creating market chart...")
    chart_image = create_stock_chart(stock_data)
    
    # Generate AI analysis
    print("🤖 Generating AI analysis...")
    ai_analysis = generate_ai_analysis(stock_data)
    
    # Create email content
    print("✍️ Creating email content...")
    from_name = os.getenv('FROM_NAME', 'Market AI Reporter')
    html_content = create_email_html(stock_data, ai_analysis, from_name)
    
    # Send email
    print("📧 Sending email...")
    email_to = os.getenv('EMAIL_TO')
    success = send_email(html_content, chart_image, email_to, from_name)
    
    if success:
        print("🎉 Morning market report sent successfully!")
    else:
        print("💥 Failed to send market report")

if __name__ == "__main__":
    main()
