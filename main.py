import os
from pathlib import Path
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from sqlmodel import SQLModel, Field, create_engine, Session, select
from datetime import datetime
import httpx
import numpy as np
from typing import Optional
import random

# --- DYNAMIC FAVICON PATHING (RESTORED) ---
FAVICON_NAME = "Luxury gold embossed logo design.png" 
DOWNLOADS_PATH = Path.home() / "Downloads" / FAVICON_NAME

# --- ENGINE CONFIG (STRICTLY UNTOUCHED) ---
sqlite_url = "sqlite:///aureusiq_final.db"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

class Ledger(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    type: str 
    amount: float
    category: str 
    is_volatile: bool = False
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))

def get_session():
    with Session(engine) as session: yield session

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

@app.on_event("startup")
def on_startup(): SQLModel.metadata.create_all(engine)

# --- FAVICON ROUTE ---
@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    target = DOWNLOADS_PATH.resolve()
    if target.exists():
        return FileResponse(target, media_type="image/png")
    return None 

# --- QUANT ADDITION: STOCHASTIC ENGINE ---
def run_quant_sim(net, margin, vol, months=6):
    paths = 10 
    mu = (margin / net) if net != 0 else 0
    sigma = max(vol, 0.1) 
    z = np.random.standard_normal((paths, months))
    returns = np.exp((mu - 0.5 * sigma**2) + sigma * z)
    
    results = np.zeros((paths, months + 1))
    results[:, 0] = net
    for t in range(1, months + 1):
        results[:, t] = results[:, t-1] * returns[:, t-1]
    return results.round(2).tolist()

# --- LOGIC (STRICTLY UNTOUCHED + QUANT ADDITIONS) ---
async def fetch_global_metrics():
    metrics = {"USD": 1560.0, "GBP": 1995.0, "inflation": 0.28} 
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=1.0)
            d = r.json()['rates']
            metrics.update({"USD": d['NGN'], "GBP": d['NGN']/d['GBP']})
    except: pass
    return metrics

@app.get("/pulse")
async def get_pulse(session: Session = Depends(get_session)):
    entries = session.exec(select(Ledger)).all()
    mkt = await fetch_global_metrics()
    total_in = sum(e.amount for e in entries if e.type == "income")
    total_out = sum(e.amount for e in entries if e.type == "expense")
    net = total_in - total_out
    margin = total_in - total_out
    wants = sum(e.amount for e in entries if e.category == "want")
    want_ratio = (wants / total_out * 100) if total_out > 0 else 0
    velocity = (total_in + total_out) / abs(net) if net != 0 else 0
    risk_exp = sum(e.amount for e in entries if e.is_volatile) / total_in if total_in > 0 else 0
    real_net = net / (1 + mkt['inflation'])
    
    # --- ADDED: QUANT SIMULATION & VaR ---
    sims = run_quant_sim(net, margin, risk_exp)
    final_vals = [p[-1] for p in sims]
    var_95 = np.percentile(final_vals, 5)

    # --- NEW QUANT METRICS INTEGRATION ---
    # 1. Probability of Ruin
    prob_ruin = (len([v for v in final_vals if v < 0]) / len(final_vals)) * 100
    
    # 2. Drawdown Analysis
    max_val = max([max(p) for p in sims]) if sims else 1
    min_val = min([min(p) for p in sims]) if sims else 1
    drawdown = ((max_val - min_val) / max_val * 100) if max_val > 0 else 0

    # 3. Financial Regime Detection
    if margin > 0 and risk_exp < 0.2: regime = "Accumulation (Safe)"
    elif margin > 0 and risk_exp >= 0.2: regime = "Aggressive Expansion"
    elif margin < 0: regime = "Distress / Capital Erosion"
    else: regime = "Stagnation"

    # 4. Volatility of Spending
    exp_vals = [e.amount for e in entries if e.type == "expense"]
    spending_vol = np.std(exp_vals) if len(exp_vals) > 1 else 0

    # 5. Financial Momentum
    momentum = (net / total_in) if total_in > 0 else 0

    # 6. Capital Efficiency Score
    cap_eff = (real_net / total_in * 100) if total_in > 0 else 0

    # 7. Behavioral Finance Layer
    bias = "Impulsive" if want_ratio > 40 else "Prudent" if want_ratio < 15 else "Balanced"

    # 8. Correlation Engine (Simulated correlation between risk exposure and net growth)
    correlation = 0.85 if risk_exp > 0.1 else 0.1 # Placeholder logic

    # 9. Financial Intelligence Index (Aureus IQ Score)
    # Weights: Margin (40%), Risk Control (30%), Efficiency (30%)
    iq_score = (min(momentum * 100, 50) + (100 - prob_ruin) * 0.3 + min(cap_eff, 20))
    iq_score = round(max(0, min(iq_score, 100)), 1)
    
    if margin < 0: advice = " Burn rate is high. Capital protection required."
    elif var_95 < net * 0.7: advice = " Quant Alert: Tail risk high. 95% VaR suggests drawdown."
    elif want_ratio > 40: advice = f" Wealth leak: {want_ratio:.1f}% on wants."
    else: advice = " Position healthy. Real value confirmed."
    
    return {
        "balances": {"NGN": net, "USD": net/mkt['USD'], "GBP": net/mkt['GBP']},
        "metrics": {
            "risk": round(risk_exp * 100, 1), 
            "wants": round(want_ratio, 1), 
            "velocity": round(velocity, 2), 
            "real_net": round(real_net, 2),
            "var": round(var_95, 2),
            "prob_ruin": round(prob_ruin, 1),
            "drawdown": round(drawdown, 1),
            "regime": regime,
            "spending_vol": round(spending_vol, 2),
            "momentum": round(momentum, 2),
            "cap_eff": round(cap_eff, 1),
            "bias": bias,
            "correlation": correlation,
            "iq_score": iq_score
        },
        "sims": sims, "advice": advice, "mkt": mkt
    }

@app.post("/log")
def log_entry(e: Ledger, session: Session = Depends(get_session)):
    session.add(e); session.commit(); return {"ok": True}

@app.get("/", response_class=HTMLResponse)
def read_root():
    return html_content

# --- UI WITH INTERACTIVE CHART ---
html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AureusIQ</title>
    <link rel="icon" type="image/png" href="http://127.0.0.1:8000/favicon.ico?v=2.1">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root { --bg: #050505; --card: #0f0f0f; --gold: #D4AF37; --bright-gold: #FFD700; --muted-gold: #8A6F2A; --text: #f0f0f0; }
        body { background: var(--bg); color: var(--text); font-family: 'Garamond', serif; padding: 15px; margin: 0; font-size: 13px; }
        .card { background: var(--card); border: 1px solid #1a1a1a; padding: 20px; border-radius: 4px; margin-bottom: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        .ai-term { border-left: 3px solid var(--gold); padding: 12px; background: linear-gradient(90deg, rgba(212, 175, 55, 0.05) 0%, transparent 100%); color: var(--bright-gold); margin: 15px 0; font-family: 'Inter', sans-serif; font-style: italic; font-size: 0.8rem; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .label { font-size: 0.6rem; color: var(--muted-gold); text-transform: uppercase; letter-spacing: 2px; }
        .val { font-size: 1.1rem; font-weight: bold; color: #fff; margin-top: 5px; }
        input, select { width: 100%; padding: 12px; margin: 8px 0; background: #000; border: 1px solid #222; color: #fff; border-radius: 0; font-family: inherit; }
        button { width: 100%; padding: 18px; background: linear-gradient(135deg, var(--muted-gold) 0%, var(--gold) 50%, var(--bright-gold) 100%); border: none; font-weight: 900; cursor: pointer; color: #000; text-transform: uppercase; letter-spacing: 3px; }
        .tab { flex: 1; padding: 10px; background: #000; border: 1px solid #1a1a1a; color: var(--muted-gold); cursor: pointer; }
        .active { border-color: var(--gold); color: var(--bright-gold); }
        .iq-circle { border: 2px solid var(--gold); border-radius: 50%; width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; margin: 0 auto; color: var(--bright-gold); font-weight: bold; font-size: 1.2rem; }
    </style>
</head>
<body>
    <div style="text-align:center; padding: 10px 0 25px 0;">
        <h1 style="color: var(--gold); letter-spacing: 8px; margin: 0; font-weight: 100;">AUREUS IQ</h1>
        <div class="iq-circle" id="iq_score">--</div>
        <div class="label" style="margin-top:5px;">Intelligence Index</div>
    </div>

    <div class="card" style="text-align:center; border-bottom: 4px solid var(--gold);">
        <div id="bal" style="font-size: 2.8rem; font-weight: 900; color: var(--bright-gold);">0.00</div>
        <div class="label">Net Balance</div>
        <div id="advice" class="ai-term">Awaiting data...</div>
    </div>

    <div class="grid">
        <div class="card"><div class="label">Regime</div><div id="regime" class="val">---</div></div>
        <div class="card"><div class="label">Prob. of Ruin</div><div id="ruin" class="val">0%</div></div>
        <div class="card"><div class="label">Max Drawdown</div><div id="drawdown" class="val">0%</div></div>
        <div class="card"><div class="label">Bias</div><div id="bias" class="val">---</div></div>
        <div class="card"><div class="label">Cap. Efficiency</div><div id="efficiency" class="val">0%</div></div>
        <div class="card"><div class="label">Spend Vol.</div><div id="spend_vol" class="val">0</div></div>
    </div>

    <div class="card">
        <canvas id="quantChart" style="max-height: 200px;"></canvas>
    </div>

    <div class="card">
        <div class="label">Log Transaction</div>
        <input type="number" id="amt" placeholder="Amount">
        <select id="cat">
            <option value="need">Need</option>
            <option value="want">Want</option>
            <option value="invest">Investment</option>
        </select>
        <select id="type">
            <option value="income">Income</option>
            <option value="expense">Expense</option>
        </select>
        <button onclick="log()">Execute Entry</button>
    </div>

    <script>
        let chart;
        async function refresh() {
            const r = await fetch('/pulse');
            const d = await r.json();
            document.getElementById('bal').innerText = d.balances.NGN.toLocaleString();
            document.getElementById('iq_score').innerText = d.metrics.iq_score;
            document.getElementById('regime').innerText = d.metrics.regime;
            document.getElementById('ruin').innerText = d.metrics.prob_ruin + '%';
            document.getElementById('drawdown').innerText = d.metrics.drawdown + '%';
            document.getElementById('bias').innerText = d.metrics.bias;
            document.getElementById('efficiency').innerText = d.metrics.cap_eff + '%';
            document.getElementById('spend_vol').innerText = d.metrics.spending_vol.toLocaleString();
            document.getElementById('advice').innerText = d.advice;

            const ctx = document.getElementById('quantChart').getContext('2d');
            if(chart) chart.destroy();
            chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [0,1,2,3,4,5,6],
                    datasets: d.sims.map((p, i) => ({
                        data: p, borderColor: i==0?'#D4AF37':'#222', borderWidth: 1, pointRadius: 0
                    }))
                },
                options: { plugins: { legend: { display: false } } }
            });
        }
        async function log() {
            await fetch('/log', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    amount: document.getElementById('amt').value,
                    category: document.getElementById('cat').value,
                    type: document.getElementById('type').value
                })
            });
            refresh();
        }
        refresh();
    </script>
</body>
</html>
"""
