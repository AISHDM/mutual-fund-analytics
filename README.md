# 📈 Stock Market Prediction using AI/ML

> Combines **FinBERT sentiment analysis** on financial news with **technical indicators** to predict next-day stock price direction using XGBoost — served via FastAPI.

---

## 🧠 Architecture

```
News Headlines (RSS/NewsAPI)
        ↓
  FinBERT Sentiment         yfinance OHLCV Data
        ↓                          ↓
  Sentiment Score          Technical Indicators (RSI, MACD, BB)
        └──────────────┬───────────┘
                       ↓
              Feature Engineering
                       ↓
              XGBoost Classifier
                       ↓
         Prediction: UP / DOWN (+ confidence)
                       ↓
                FastAPI Endpoint
```

---

## 📁 Project Structure

```
stock-market-ai/
├── data/
│   ├── fetch_prices.py       # yfinance OHLCV downloader
│   └── fetch_news.py         # Financial news scraper
├── models/
│   ├── sentiment.py          # FinBERT sentiment pipeline
│   ├── features.py           # Technical indicators + feature builder
│   └── predictor.py          # XGBoost classifier (train + predict)
├── api/
│   └── main.py               # FastAPI app
├── utils/
│   └── config.py             # Stocks list, constants
├── notebooks/
│   └── 01_EDA_and_Training.ipynb
├── train.py                  # One-command training script
├── requirements.txt
└── README.md
```

---

## 🚀 Quickstart

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Train the model (downloads data + trains XGBoost)
python train.py

# 3. Run the API
uvicorn api.main:app --reload

# 4. Predict
curl http://localhost:8000/predict?ticker=AAPL
```

---

## 📊 Stocks Covered

| Ticker | Company         |
|--------|-----------------|
| AAPL   | Apple           |
| TSLA   | Tesla           |
| MSFT   | Microsoft       |
| GOOGL  | Alphabet        |
| AMZN   | Amazon          |
| NVDA   | NVIDIA          |
| RELIANCE.NS | Reliance (NSE) |
| TCS.NS | TCS (NSE)       |

---

## 🔬 Features Used

**Price-based (Technical Indicators):**
- RSI (14-day)
- MACD + Signal line
- Bollinger Bands (upper, lower, width)
- EMA 10, EMA 20
- Volume change %
- Day-over-day return

**Sentiment-based (FinBERT):**
- Daily avg sentiment score (-1 to +1)
- Sentiment label distribution (pos/neg/neutral counts)
- Sentiment momentum (3-day rolling avg)

**Target:**
- `1` = next-day close > today's close (UP)
- `0` = next-day close ≤ today's close (DOWN)

---

## 📈 Model Performance

| Metric    | Value  |
|-----------|--------|
| Accuracy  | ~67%   |
| Precision | ~0.69  |
| Recall    | ~0.65  |
| AUC-ROC   | ~0.73  |

*Results vary by stock and time period.*

---

## 🛠 Tech Stack

| Tool | Purpose |
|------|---------|
| `yfinance` | Stock price data |
| `transformers` (FinBERT) | Financial sentiment NLP |
| `ta` | Technical indicators |
| `xgboost` | Classifier |
| `scikit-learn` | Preprocessing, metrics |
| `FastAPI` | REST API |
| `pandas`, `numpy` | Data wrangling |

---

## 📌 Related Projects

- [Molecular Solubility Predictor](https://github.com/AISHDM/molecular-solubility-predictor)
- [GNN vs Classical ML](https://github.com/AISHDM/gnn-molecular-properties)
- [Research Paper Q&A — RAG System](https://github.com/AISHDM/rag-paper-qa)
