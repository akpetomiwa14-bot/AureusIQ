# Aureus IQ — Quantitative Personal Risk & Intelligence Engine

Aureus IQ is a full-stack quantitative personal finance application that evaluates personal cash flows through stochastic risk modeling, tail-risk metrics, real-time macroeconomic adjustments, and behavioral analysis.

Instead of static ledger tracking, Aureus IQ models future capital trajectories using Monte Carlo simulations, calculates Value at Risk (VaR), tracks inflation-adjusted real value, and dynamically classifies financial regimes.

---

## Technical Highlights

* **Stochastic Monte Carlo Engine**: Simulates multi-month capital growth trajectories using standard normal distribution dynamics to forecast potential portfolio paths.
* **Tail-Risk & Liquidity Metrics**: Dynamically measures 95% Value at Risk (VaR 95), Maximum Drawdown percentage, and Probability of Ruin.
* **Macroeconomic Integration**: Connects to real-time Forex APIs (USD/GBP/NGN) and applies real inflation adjustments to compute true real net worth.
* **Regime & Behavioral Intelligence**: Automatically detects operational financial regimes (Accumulation, Expansion, Capital Erosion) and identifies spending biases based on expense distribution.
* **Composite Financial Intelligence Score**: Calculates a unified Aureus IQ index evaluating capital efficiency, momentum, and downside risk protection.
* **Full-Stack Implementation**: Asynchronous REST backend built with FastAPI, SQLModel (SQLite), HTTPX, and NumPy, paired with a lightweight interactive HTML/CSS/Chart.js frontend.

---

## Core Quantitative Architecture

### 1. Geometric Brownian Dynamics (Simulations)
The stochastic engine projects future capital balance across 10 distinct simulation paths over a 6-month horizon using drift $\mu$ (margin efficiency) and spending volatility $\sigma$:

$$S_{t+1} = S_t \times \exp\left( (\mu - 0.5\sigma^2) + \sigma Z \right)$$

where $Z \sim \mathcal{N}(0, 1)$.

### 2. Tail Risk Analytics
* **Value at Risk (VaR 95%)**: Evaluates downside loss potential at the 5th percentile outcome across terminal simulation states.
* **Probability of Ruin**: Tracks the percentage of simulated terminal balances falling below zero capital:

$$\text{Probability of Ruin} = \left( \frac{\text{Count}(V_{\text{final}} < 0)}{N_{\text{paths}}} \right) \times 100$$

* **Capital Efficiency**: Evaluates real inflation-adjusted liquidity growth against gross inbound cash flows:

$$\text{Capital Efficiency} = \left( \frac{\text{Real Net Balance}}{\text{Total Income}} \right) \times 100$$

---

## Tech Stack

* **Backend**: Python, FastAPI, SQLModel, SQLite, NumPy, HTTPX, Uvicorn
* **Frontend**: HTML5, Modern CSS, JavaScript (ES6+), Chart.js
* **Data Sources**: Dynamic Foreign Exchange Rate APIs

---

## Local Deployment Instructions

### Prerequisites
* Python 3.9+
* `pip` package manager

### Setup

1. Clone the repository:
   ```bash
   git clone [https://github.com/YOUR_USERNAME/aureus-iq.git](https://github.com/YOUR_USERNAME/aureus-iq.git)
   cd aureus-iq
