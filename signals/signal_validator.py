"""
Signal validation utilities for webhooks
Provides comprehensive validation for trading signals
"""
import re
import logging
from decimal import Decimal, InvalidOperation

logger = logging.getLogger('webhook')


def validate_signal_data(data):
    """
    Comprehensive validation of signal data with detailed error messages.
    
    Args:
        data: Dictionary containing signal data
    
    Returns:
        dict: {'valid': bool, 'errors': list, 'warnings': list}
    """
    errors = []
    warnings = []
    
    # 1. Validate symbol format (A-Z, digits, optional slash)
    symbol = str(data.get('symbol', '')).strip().upper()
    if not re.match(r'^[A-Z0-9/]+$', symbol):
        errors.append(f"Invalid symbol format: '{symbol}'. Must contain only A-Z, 0-9, and '/' characters.")
    elif len(symbol) < 2:
        errors.append(f"Symbol too short: '{symbol}'. Must be at least 2 characters.")
    elif len(symbol) > 20:
        errors.append(f"Symbol too long: '{symbol}'. Maximum 20 characters.")
    
    # 2. Validate confidence (0-100)
    try:
        confidence = float(data.get('confidence', -1))
        if confidence < 0 or confidence > 100:
            errors.append(f"Confidence must be between 0 and 100, got: {confidence}")
        elif confidence < 40:
            warnings.append(f"Low confidence detected: {confidence}%. Consider skipping low-confidence signals.")
    except (ValueError, TypeError):
        errors.append(f"Invalid confidence value: {data.get('confidence')}")
    
    # 3. Validate side
    side = str(data.get('side', '')).strip().lower()
    if side not in ['buy', 'sell']:
        errors.append(f"Invalid side: '{side}'. Must be 'buy' or 'sell'.")
    
    # 4. Validate price, SL, TP
    try:
        price = Decimal(str(data.get('price', 0))) if data.get('price') else None
        sl = Decimal(str(data.get('sl', 0)))
        tp = Decimal(str(data.get('tp', 0)))
        
        # Check for zero or negative values
        if sl <= 0:
            errors.append(f"Stop loss must be positive, got: {sl}")
        if tp <= 0:
            errors.append(f"Take profit must be positive, got: {tp}")
        
        # 5. SL/TP sanity checks
        if price and sl > 0 and tp > 0:
            sl_tp_errors = validate_sl_tp_logic(side, price, sl, tp)
            errors.extend(sl_tp_errors)
        elif sl > 0 and tp > 0:
            # Check SL != TP at minimum
            if sl == tp:
                errors.append("Stop loss and take profit cannot be equal")
    
    except (InvalidOperation, ValueError, TypeError) as e:
        errors.append(f"Invalid price/SL/TP format: {e}")
    
    # 6. Validate strategy
    strategy = str(data.get('strategy', '')).strip()
    if not strategy:
        errors.append("Strategy name is required")
    elif len(strategy) > 50:
        errors.append(f"Strategy name too long: '{strategy}'. Maximum 50 characters.")
    
    # 7. Validate regime
    regime = str(data.get('regime', '')).strip()
    valid_regimes = ['Trend', 'Breakout', 'MeanReversion', 'Squeeze']
    if regime not in valid_regimes:
        errors.append(f"Invalid regime: '{regime}'. Must be one of: {', '.join(valid_regimes)}")
    
    # 8. Validate timeframe
    timeframe = str(data.get('timeframe', '')).strip()
    if not timeframe:
        errors.append("Timeframe is required")
    elif not re.match(r'^[0-9]+[mhdwMD]$', timeframe):
        warnings.append(f"Non-standard timeframe format: '{timeframe}'. Expected format like '1h', '15m', '4h'.")
    
    # 9. Check for required fields
    required_fields = ['symbol', 'timeframe', 'side', 'sl', 'tp', 'confidence', 'strategy', 'regime']
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        errors.append(f"Missing required fields: {', '.join(missing_fields)}")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def validate_sl_tp_logic(side, price, sl, tp):
    """
    Validate stop loss and take profit logic based on trade direction.
    
    For BUY trades:
        - SL must be below entry price (sl < price)
        - TP must be above entry price (tp > price)
        - Logic: sl < price < tp
    
    For SELL trades:
        - SL must be above entry price (sl > price)
        - TP must be below entry price (tp < price)
        - Logic: tp < price < sl
    
    Args:
        side: 'buy' or 'sell'
        price: Entry price (Decimal)
        sl: Stop loss (Decimal)
        tp: Take profit (Decimal)
    
    Returns:
        list: List of error messages (empty if valid)
    """
    errors = []
    
    if side == 'buy':
        # BUY: sl < price < tp
        if sl >= price:
            errors.append(
                f"BUY trade: Stop loss ({sl}) must be below entry price ({price}). "
                f"Current difference: {price - sl}"
            )
        if tp <= price:
            errors.append(
                f"BUY trade: Take profit ({tp}) must be above entry price ({price}). "
                f"Current difference: {tp - price}"
            )
        
        # Calculate risk:reward ratio
        if sl < price < tp:
            risk = float(price - sl)
            reward = float(tp - price)
            rr_ratio = reward / risk if risk > 0 else 0
            
            if rr_ratio < 1.0:
                errors.append(
                    f"BUY trade: Risk:Reward ratio is {rr_ratio:.2f}. "
                    f"Risk={risk:.5f}, Reward={reward:.5f}. Consider improving R:R to at least 1:1."
                )
    
    elif side == 'sell':
        # SELL: tp < price < sl
        if sl <= price:
            errors.append(
                f"SELL trade: Stop loss ({sl}) must be above entry price ({price}). "
                f"Current difference: {sl - price}"
            )
        if tp >= price:
            errors.append(
                f"SELL trade: Take profit ({tp}) must be below entry price ({price}). "
                f"Current difference: {price - tp}"
            )
        
        # Calculate risk:reward ratio
        if tp < price < sl:
            risk = float(sl - price)
            reward = float(price - tp)
            rr_ratio = reward / risk if risk > 0 else 0
            
            if rr_ratio < 1.0:
                errors.append(
                    f"SELL trade: Risk:Reward ratio is {rr_ratio:.2f}. "
                    f"Risk={risk:.5f}, Reward={reward:.5f}. Consider improving R:R to at least 1:1."
                )
    
    return errors


def sanitize_signal_data(data):
    """
    Sanitize and normalize signal data before saving to database.
    
    Args:
        data: Dictionary containing signal data
    
    Returns:
        dict: Sanitized data
    """
    sanitized = {}
    
    # Normalize symbol to uppercase
    sanitized['symbol'] = str(data.get('symbol', '')).strip().upper()
    
    # Normalize side to lowercase
    sanitized['side'] = str(data.get('side', '')).strip().lower()
    
    # Normalize strategy and regime
    sanitized['strategy'] = str(data.get('strategy', '')).strip()
    sanitized['regime'] = str(data.get('regime', '')).strip()
    
    # Normalize timeframe
    sanitized['timeframe'] = str(data.get('timeframe', '')).strip()
    
    # Convert numbers to Decimal
    for field in ['price', 'sl', 'tp']:
        value = data.get(field)
        if value is not None:
            try:
                sanitized[field] = Decimal(str(value))
            except (InvalidOperation, ValueError):
                sanitized[field] = None
        else:
            sanitized[field] = None
    
    # Convert confidence to float
    try:
        sanitized['confidence'] = float(data.get('confidence', 50))
    except (ValueError, TypeError):
        sanitized['confidence'] = 50.0
    
    # Copy optional fields
    sanitized['timestamp'] = data.get('timestamp', '')
    sanitized['session'] = data.get('session', '')
    
    return sanitized
