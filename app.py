import streamlit as st
import pandas as pd
import json

from src.agent import ExecutionDisciplineAgent

# MUST be the first Streamlit call
st.set_page_config(page_title="Execution Discipline Agent", layout="wide")

# Temporary fingerprint (safe now)
st.error("🚨 EXECUTION DISCIPLINE AGENT — THIS FILE IS RUNNING 🚨")

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

regime_label = st.text_input(
    "Current Market Regime",
    value="Risk-Off",
    help="Paste from MarketRegimeAgent output"
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

        st.subheader("🚨 Violations")
        if report.violations:
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
