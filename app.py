import streamlit as st
import pandas as pd
import json
import io
from pathlib import Path

from src.agent import ExecutionDisciplineAgent
from src.coaching import generate_coaching_summary

def get_regime_from_market_regime_agent() -> str:
    """
    Attempt to read last_regime_label from MarketRegimeAgent state file.
    Returns default "Risk-Off" if file doesn't exist or can't be read.
    """
    default_regime = "Risk-Off"
    
    # Path to MarketRegimeAgent state file (relative to current directory)
    regime_agent_path = Path(__file__).parent.parent / "Market-Regime-Agent" / "state" / "memory.json"
    
    try:
        if not regime_agent_path.exists():
            return default_regime
        
        # Read and parse JSON
        with open(regime_agent_path, 'r') as f:
            regime_data = json.load(f)
        
        # Extract last_regime_label
        last_regime = regime_data.get("last_regime_label")
        
        if last_regime and isinstance(last_regime, str):
            return last_regime
        
        return default_regime
        
    except (json.JSONDecodeError, KeyError, IOError, OSError):
        # Gracefully handle any errors: file doesn't exist, invalid JSON, missing key, etc.
        return default_regime

def violations_to_csv(violations) -> str:
    """
    Convert violations list to CSV format.
    Returns CSV string with columns: trade_index, violation_type, detail
    """
    if not violations:
        return "trade_index,violation_type,detail\n"
    
    # Create CSV content
    csv_lines = ["trade_index,violation_type,detail"]
    for v in violations:
        # Escape quotes in CSV fields (double quotes for CSV standard)
        violation_type_escaped = v.violation_type.replace('"', '""')
        detail_escaped = v.detail.replace('"', '""')
        csv_lines.append(f'{v.trade_index},"{violation_type_escaped}","{detail_escaped}"')
    
    return "\n".join(csv_lines)

# MUST be the first Streamlit call
st.set_page_config(page_title="Execution Discipline Agent", layout="wide")

st.title("🧭 Execution Discipline Agent (v1)")
st.caption("Did I follow my trading plan — given the market regime?")

# --- File uploads ---
trades_file = st.file_uploader(
    "Upload trades CSV",
    type=["csv"],
    help="Trade execution log (offline only)"
)

plan_file = st.file_uploader(
    "Upload trading plan JSON",
    type=["json"],
    help="Explicit trading rules"
)

# Try to auto-import regime from MarketRegimeAgent
default_regime = get_regime_from_market_regime_agent()

regime_label = st.text_input(
    "Current Market Regime",
    value=default_regime,
    help="Auto-imported from MarketRegimeAgent if available, or paste manually"
)

# Optional LLM coaching feature
enable_coaching = st.checkbox(
    "🤖 Enable LLM Coaching Summary",
    value=False,
    help="Generate behavioral coaching insights using AI (requires OPENAI_API_KEY environment variable)"
)

# --- Run agent ---
if trades_file is not None and plan_file is not None:
    try:
        # Reset file pointers to beginning
        trades_file.seek(0)
        plan_file.seek(0)
        
        # Read CSV file
        try:
            trades = pd.read_csv(trades_file)
            st.success(f"✅ Loaded {len(trades)} trades from CSV")
        except Exception as csv_error:
            st.error(f"❌ Error reading CSV file: {str(csv_error)}")
            st.exception(csv_error)
            raise
        
        # Read JSON file
        try:
            plan = json.load(plan_file)
            st.success("✅ Loaded trading plan JSON")
        except json.JSONDecodeError as json_error:
            st.error(f"❌ Invalid JSON format: {str(json_error)}")
            st.exception(json_error)
            raise
        except Exception as json_error:
            st.error(f"❌ Error reading JSON file: {str(json_error)}")
            st.exception(json_error)
            raise

        # Validate required plan fields
        if "allowed_regimes" not in plan:
            st.error("❌ Trading plan missing required field: 'allowed_regimes'")
            st.stop()

        # Run agent
        agent = ExecutionDisciplineAgent()
        report = agent.run(trades, plan, regime_label)

        st.subheader("📊 Discipline Report")
        st.metric("Compliance Score", report.compliance_score)
        st.metric("Regime Mismatch Rate", report.regime_mismatch_rate)
        
        # Compliance trend
        trend_emoji = {
            "improving": "📈",
            "worsening": "📉",
            "flat": "➡️"
        }
        trend_text = {
            "improving": "Compliance is improving over the last 5 runs",
            "worsening": "Compliance is worsening over the last 5 runs",
            "flat": "Compliance trend is flat over the last 5 runs"
        }
        emoji = trend_emoji.get(report.compliance_trend, "➡️")
        text = trend_text.get(report.compliance_trend, "Insufficient data to determine trend")
        st.caption(f"{emoji} **Trend**: {text}")

        # Violation frequency summary
        st.subheader("📌 Most Common Discipline Issues")
        if report.violation_summary:
            for k, v in sorted(report.violation_summary.items(), key=lambda x: x[1], reverse=True):
                st.write(f"- **{k}**: {v}")
        else:
            st.write("No issues detected.")

        # Optional LLM coaching summary
        if enable_coaching:
            with st.spinner("Generating coaching insights..."):
                coaching_summary = generate_coaching_summary(
                    report.violations,
                    report.violation_summary,
                    report.compliance_score
                )
            
            if coaching_summary:
                st.subheader("💡 Behavioral Coaching")
                st.info(coaching_summary)
            elif enable_coaching:
                st.warning("⚠️ LLM coaching unavailable. Ensure OPENAI_API_KEY is set in your environment.")

        st.subheader("🚨 Violations")
        if report.violations:
            # CSV export button
            csv_data = violations_to_csv(report.violations)
            st.download_button(
                label="📥 Download Violations as CSV",
                data=csv_data,
                file_name="violations.csv",
                mime="text/csv",
                help="Download all violations as a CSV file"
            )
            
            for v in report.violations:
                st.write(
                    f"**Trade #{v.trade_index} — {v.violation_type}**: {v.detail}"
                )
        else:
            st.success("No violations detected. Discipline intact 🎯")

    except Exception as e:
        st.error("❌ Error processing files")
        st.exception(e)
        st.info("💡 Tip: Make sure your CSV has the required columns: date, symbol, side, entry_price, exit_price, shares, stop_price")
else:
    st.info("Upload both a trades CSV and a plan JSON to run the agent.")
