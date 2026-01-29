# 🧭 Execution Discipline Agent (v1)

> A deterministic agent that evaluates whether trades were executed according to a predefined trading plan — conditioned on the current market regime.

**⚠️ Important:** This agent measures **process compliance**, not PnL. Built to diagnose behavior, not generate signals.

---

## 📋 Table of Contents

- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Input Formats](#-input-formats)
- [Output](#-output)
- [Architecture](#-architecture)
- [Usage Examples](#-usage-examples)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Features

- ✅ **Rule-based evaluation** — No AI/ML, deterministic compliance checking
- 📊 **Regime-aware analysis** — Validates trades against market regime constraints
- 🛡️ **Stop-loss validation** — Ensures stop-loss orders are properly set
- 💾 **Persistent memory** — Tracks compliance history over time
- 🚫 **No external APIs** — Fully offline, no OpenAI or external dependencies
- 🎯 **Process-focused** — Measures discipline, not performance

---

## 🚀 Installation

### Prerequisites

- Python 3.7+
- pip

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Execution-Discipline-Agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Streamlit app**
   ```bash
   streamlit run app.py
   ```

4. **Open your browser**
   - The app will automatically open at `http://localhost:8501`
   - If not, navigate to the URL shown in the terminal

---

## 🎯 Quick Start

1. **Prepare your files:**
   - 📄 **Trades CSV** — Your trade execution log (see format below)
   - 📋 **Trading Plan JSON** — Your trading rules (see format below)

2. **Launch the app:**
   ```bash
   streamlit run app.py
   ```

3. **Upload files:**
   - Upload your trades CSV file
   - Upload your trading plan JSON file
   - Enter the current market regime label (e.g., "Risk-On", "Risk-Off")

4. **View results:**
   - Compliance score (0.0 to 1.0)
   - Regime mismatch rate
   - Detailed violation list

---

## 📥 Input Formats

### 📄 Trades CSV Format

Your trades CSV must include the following columns:

| Column | Description | Example | Required |
|--------|-------------|---------|----------|
| `date` | Trade date | `2025-08-01` | ✅ |
| `symbol` | Trading symbol | `SPY` | ✅ |
| `side` | Trade direction | `LONG` or `SHORT` | ✅ |
| `entry_price` | Entry price | `530.00` | ✅ |
| `exit_price` | Exit price | `535.00` | ✅ |
| `shares` | Number of shares | `100` | ✅ |
| `stop_price` | Stop-loss price | `525.00` | ⚠️ (if `stop_required: true`) |

**Example:**
```csv
date,symbol,side,entry_price,exit_price,shares,stop_price
2025-08-01,SPY,LONG,530,535,100,525
2025-08-02,QQQ,LONG,470,465,120,
```

### 📋 Trading Plan JSON Format

Your trading plan JSON must include:

```json
{
  "allowed_regimes": ["Risk-On", "Risk-Off"],
  "stop_required": true,
  "risk_per_trade_pct": 0.5,
  "max_position_pct": 10,
  "max_stop_pct": 2.0
}
```

**Required Fields:**
- `allowed_regimes` (array): List of market regimes where trading is allowed
- `stop_required` (boolean): Whether stop-loss orders are mandatory

**Optional Fields:**
- `risk_per_trade_pct`: Maximum risk per trade percentage
- `max_position_pct`: Maximum position size percentage
- `max_stop_pct`: Maximum stop-loss percentage

**Example:**
```json
{
  "risk_per_trade_pct": 0.5,
  "max_position_pct": 10,
  "allowed_regimes": ["Risk-On"],
  "stop_required": true,
  "max_stop_pct": 2.0
}
```

### 🏷️ Market Regime Label

Enter the current market regime as a text string. Common values:
- `Risk-On`
- `Risk-Off`
- `Neutral`
- `Volatile`

---

## 📤 Output

The agent generates a **Discipline Report** containing:

### 📊 Metrics

- **Compliance Score** (0.0 - 1.0)
  - `1.0` = Perfect compliance (no violations)
  - `0.0` = Complete non-compliance
  - Calculated as: `1.0 - (violations / total_trades)`

- **Regime Mismatch Rate** (0.0 - 1.0)
  - Percentage of trades executed in non-allowed regimes

### 🚨 Violations

Each violation includes:
- **Trade Index**: Which trade violated the rule
- **Violation Type**: 
  - `Regime Mismatch` — Trade executed in non-allowed regime
  - `Missing Stop` — Required stop-loss not provided
- **Detail**: Human-readable explanation

---

## 🏗️ Architecture

```
Execution-Discipline-Agent/
├── app.py                 # Streamlit web interface
├── src/
│   ├── agent.py          # Main agent logic
│   ├── rules.py          # Compliance rule checkers
│   ├── schemas.py        # Data models
│   └── memory.py         # Persistent state management
├── data/
│   ├── trades.example.csv    # Example trades file
│   └── plan.example.json     # Example plan file
├── state/
│   └── memory.json       # Persistent compliance history
└── requirements.txt      # Python dependencies
```

### 🔍 Key Components

- **`ExecutionDisciplineAgent`**: Main agent class that orchestrates compliance checking
- **`check_regime_allowed()`**: Validates trades against allowed regimes
- **`check_missing_stops()`**: Ensures stop-loss orders are present when required
- **Memory System**: Tracks compliance history in `state/memory.json`

---

## 💡 Usage Examples

### Example 1: Command Line Testing

```python
import pandas as pd
import json
from src.agent import ExecutionDisciplineAgent

# Load data
trades = pd.read_csv("data/trades.example.csv")
plan = json.load(open("data/plan.example.json"))

# Run agent
agent = ExecutionDisciplineAgent()
report = agent.run(trades, plan, regime_label="Risk-Off")

# View results
print(f"Compliance Score: {report.compliance_score}")
for v in report.violations:
    print(f"Trade #{v.trade_index}: {v.violation_type} - {v.detail}")
```

### Example 2: Web Interface

1. Run `streamlit run app.py`
2. Upload `data/trades.example.csv`
3. Upload `data/plan.example.json`
4. Enter regime: `Risk-Off`
5. View the compliance report

---

## 🔧 Troubleshooting

### ❌ File Upload 403 Error

If you see `AxiosError: Request failed with status code 403`:

1. **Restart Streamlit** — Stop the server (Ctrl+C) and restart:
   ```bash
   streamlit run app.py
   ```

2. **Clear browser cache** — Hard refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)

3. **Check config** — Ensure `.streamlit/config.toml` has `enableXsrfProtection = false`

### ❌ CSV Parsing Errors

- **Missing columns**: Ensure your CSV has all required columns (see [Input Formats](#-input-formats))
- **Invalid data types**: Check that prices and shares are numeric
- **Empty file**: Ensure the CSV has at least one data row (not just headers)

### ❌ JSON Parsing Errors

- **Invalid JSON**: Validate your JSON using a JSON validator
- **Missing fields**: Ensure `allowed_regimes` is present in your plan
- **Wrong data types**: `allowed_regimes` must be an array, `stop_required` must be boolean

### ❌ Memory File Errors

If you see errors about `state/memory.json`:

- The file is created automatically on first run
- Ensure the `state/` directory exists or is writable
- Delete `state/memory.json` to reset history

---

## 📝 Notes

- **Offline Only**: This agent does not connect to external APIs or services
- **Deterministic**: Same inputs always produce the same outputs
- **Process Focus**: Measures trading discipline, not profitability
- **Memory Persistence**: Compliance history is saved to `state/memory.json`

---

## 📄 License

[Add your license information here]

---

## 🤝 Contributing

[Add contribution guidelines here]

---

**Built to diagnose behavior, not generate signals.** 🎯
