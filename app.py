from flask import Flask, render_template, request, jsonify, send_file
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from datetime import datetime
import io
import requests
from bs4 import BeautifulSoup
import random  # For dummy data simulation
from prophet import Prophet  # For AI predictions
import os  # For environment variables

app = Flask(__name__)

portfolio = {}
user_scores = {}  # For gamification
eco_scores = {
    "AAPL": {"score": 75, "carbon": 4500},
    "MSFT": {"score": 80, "carbon": 3800},
    "TSLA": {"score": 95, "carbon": 2000}
}

def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        history = stock.history(period="30d")
        current_price = info.get('regularMarketPrice', history['Close'][-1])
        sma_20 = history['Close'].rolling(window=20).mean().iloc[-1]
        rsi = RSIIndicator(history['Close'], window=14).rsi().iloc[-1]
        chart_data = history['Close'].tail(30).to_list()
        
        # AI Prediction (simulated)
        df = pd.DataFrame({"ds": history.index, "y": history["Close"]})
        model = Prophet(yearly_seasonality=True)
        model.fit(df)
        future = model.make_future_dataframe(periods=7)  # 7-day forecast
        forecast = model.predict(future)
        prediction = round(forecast["yhat"].iloc[-1], 2)
        
        return {
            "name": info.get('longName', ticker),
            "price": round(current_price, 2),
            "sma_20": round(sma_20, 2),
            "rsi": round(rsi, 2),
            "decision": "Buy" if current_price < sma_20 else "Sell" if current_price > sma_20 else "Hold",
            "volume": info.get('volume', 0),
            "change": round(((current_price - history['Close'].iloc[-2]) / history['Close'].iloc[-2]) * 100, 2),
            "chart_data": chart_data,
            "prediction": prediction,
            "eco_score": eco_scores.get(ticker, {"score": 50, "carbon": 5000})
        }
    except Exception as e:
        return None

def get_stock_news(ticker):
    url = f"https://www.google.com/search?q={ticker}+stock+news&tbm=nws"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    news_items = soup.select("div.BNeawe a")[:3]
    return [{"title": item.text, "link": item['href']} for item in news_items]

def get_financial_tips(user_data=None):
    tips = [
        "Save 10% of your income monthly for a rainy day!",
        "Consider diversifying with international stocks.",
        "Check your portfolio’s eco-impact weekly."
    ]
    return random.choice(tips)

@app.route("/", methods=["GET", "POST"])
def home():
    error = None
    if request.method == "POST":
        ticker = request.form["ticker"].upper().strip()
        data = get_stock_data(ticker)
        if data:
            portfolio[ticker] = data
        else:
            error = f"Invalid ticker: {ticker}"
    
    news = {ticker: get_stock_news(ticker) for ticker in portfolio.keys()}
    ai_tip = get_financial_tips()
    return render_template("index.html", portfolio=portfolio, news=news, error=error, timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ai_tip=ai_tip)

@app.route("/remove/<ticker>")
def remove_stock(ticker):
    portfolio.pop(ticker, None)
    return jsonify({"status": "success"})

@app.route("/export")
def export_portfolio():
    if not portfolio:
        return "Portfolio is empty!", 400
    df = pd.DataFrame(portfolio).T
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer)
    return send_file(
        io.BytesIO(csv_buffer.getvalue().encode('utf-8')),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"kalilfin_portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))