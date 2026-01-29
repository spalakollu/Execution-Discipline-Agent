import pandas as pd
import json
from src.agent import ExecutionDisciplineAgent

trades = pd.read_csv("data/trades.example.csv")
plan = json.load(open("data/plan.example.json"))

agent = ExecutionDisciplineAgent()
report = agent.run(trades, plan, regime_label="Risk-Off")

print(report.compliance_score)
for v in report.violations:
    print(v.violation_type, v.detail)
