import pandas as pd
from typing import List, Dict
from .schemas import Violation

def check_regime_allowed(
    trades: pd.DataFrame,
    allowed_regimes: List[str],
    current_regime: str
) -> List[Violation]:
    violations = []
    if current_regime not in allowed_regimes:
        for i in range(len(trades)):
            violations.append(
                Violation(
                    trade_index=i,
                    violation_type="Regime Mismatch",
                    detail=f"Trade taken during {current_regime} regime"
                )
            )
    return violations

def check_missing_stops(trades: pd.DataFrame) -> List[Violation]:
    violations = []
    for i, row in trades.iterrows():
        if pd.isna(row.get("stop_price")):
            violations.append(
                Violation(
                    trade_index=i,
                    violation_type="Missing Stop",
                    detail="Stop required but not provided"
                )
            )
    return violations

def check_position_sizing(
    trades: pd.DataFrame,
    plan: Dict,
    current_regime: str
) -> List[Violation]:
    violations = []
    
    # Check if position limits are configured
    position_limits = plan.get("position_limits_by_regime")
    account_size = plan.get("account_size")
    
    if position_limits is None or account_size is None:
        return violations
    
    # Get the limit for the current regime
    regime_limit_pct = position_limits.get(current_regime)
    if regime_limit_pct is None:
        return violations
    
    # Calculate position size and check against limit
    for i, row in trades.iterrows():
        shares = row.get("shares")
        entry_price = row.get("entry_price")
        
        # Skip if required data is missing
        if pd.isna(shares) or pd.isna(entry_price):
            continue
        
        # Calculate position size
        position_size = shares * entry_price
        
        # Calculate position as percentage of account
        position_pct = (position_size / account_size) * 100
        
        # Check if exceeds regime limit
        if position_pct > regime_limit_pct:
            violations.append(
                Violation(
                    trade_index=i,
                    violation_type="Oversized for Regime",
                    detail=f"Position size {position_pct:.2f}% exceeds {regime_limit_pct}% limit for {current_regime} regime (position: ${position_size:,.2f})"
                )
            )
    
    return violations

def check_oversized_for_regime(
    trades: pd.DataFrame,
    account_size: float,
    position_limits_by_regime: dict,
    current_regime: str
) -> List[Violation]:
    violations = []

    if not account_size or account_size <= 0:
        return violations

    # Find an applicable limit:
    # - exact match (e.g., "Risk-Off")
    # - or prefix match (e.g., "Risk-Off / High Vol / ...")
    limit_pct = None
    if current_regime in position_limits_by_regime:
        limit_pct = position_limits_by_regime[current_regime]
    else:
        for k, v in position_limits_by_regime.items():
            if isinstance(k, str) and current_regime.startswith(k):
                limit_pct = v
                break

    if limit_pct is None:
        return violations

    max_value = (limit_pct / 100.0) * account_size

    for i, row in trades.iterrows():
        entry = row.get("entry_price")
        shares = row.get("shares")

        if pd.isna(entry) or pd.isna(shares):
            continue

        position_value = float(entry) * float(shares)
        if position_value > max_value:
            violations.append(
                Violation(
                    trade_index=i,
                    violation_type="Oversized for Regime",
                    detail=(
                        f"Position value ${position_value:,.0f} exceeds "
                        f"{limit_pct:.1f}% of account (${max_value:,.0f}) in regime '{current_regime}'."
                    )
                )
            )

    return violations

def check_r_multiple(trades: pd.DataFrame) -> List[Violation]:
    """
    Check R-multiple calculations and flag Early Exit and Late Exit violations.
    
    R-multiple formula: R = (exit_price - entry_price) / (entry_price - stop_price)
    
    Violations:
    - Early Exit: R < 0.5 (exited too early, didn't let trade run)
    - Late Exit: Trade hit stop after having >= 1R unrealized gain
    """
    violations = []
    
    for i, row in trades.iterrows():
        entry_price = row.get("entry_price")
        exit_price = row.get("exit_price")
        stop_price = row.get("stop_price")
        side = row.get("side", "LONG").upper()
        
        # Skip if required data is missing
        if pd.isna(entry_price) or pd.isna(exit_price) or pd.isna(stop_price):
            continue
        
        # Calculate R-multiple
        # R = (exit_price - entry_price) / (entry_price - stop_price)
        risk = entry_price - stop_price
        
        # Handle both LONG and SHORT positions
        if side == "SHORT":
            # For SHORT: entry > exit is profit, stop > entry is risk
            risk = stop_price - entry_price
            if abs(risk) < 0.0001:  # Avoid division by zero
                continue
            r_multiple = (entry_price - exit_price) / risk
        else:
            # For LONG: exit > entry is profit, entry > stop is risk
            if abs(risk) < 0.0001:  # Avoid division by zero
                continue
            r_multiple = (exit_price - entry_price) / risk
        
        # Check for Early Exit: R < 0.5 (but not negative, which means stop was hit)
        if 0 <= r_multiple < 0.5:
            violations.append(
                Violation(
                    trade_index=i,
                    violation_type="Early Exit",
                    detail=f"Exited at {r_multiple:.2f}R (less than 0.5R threshold). Entry: ${entry_price:.2f}, Exit: ${exit_price:.2f}, Stop: ${stop_price:.2f}"
                )
            )
        
        # Check for Late Exit: Trade hit stop (exit_price == stop_price)
        # This indicates the trade reversed from profit back to stop loss
        # Note: Without peak price data, we flag all stop hits as potential late exits
        # The assumption is that if a stop was hit, the trade likely had unrealized gains that were given back
        hit_stop = abs(exit_price - stop_price) < 0.01  # Allow small floating point differences
        
        if hit_stop and abs(risk) > 0.01:  # Hit stop and risk was meaningful
            # For Late Exit: We hit the stop, which suggests we should have exited earlier
            # when the trade was profitable (>= 1R). Since we don't have peak price data,
            # we flag all stop hits as potential late exits.
            violations.append(
                Violation(
                    trade_index=i,
                    violation_type="Late Exit",
                    detail=f"Hit stop loss at {r_multiple:.2f}R. Trade likely had >= 1R unrealized gain before reversing. Entry: ${entry_price:.2f}, Exit: ${exit_price:.2f}, Stop: ${stop_price:.2f}"
                )
            )
    
    return violations
