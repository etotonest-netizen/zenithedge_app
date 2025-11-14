"""
Engine Visuals Generator
========================
Generates chart overlays for trading signals (boxes, labels, arrows).

Output format compatible with TradingView Lightweight Charts and Plotly.

Features:
- Order Block rectangles
- Fair Value Gap boxes
- Entry point markers
- Stop Loss / Take Profit lines
- Direction arrows
- Structure labels (BOS, CHoCH, etc.)
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


def generate_signal_visuals(signal_obj, strategy_metadata: Dict) -> Dict:
    """
    Generate chart overlay visuals for a signal.
    
    Args:
        signal_obj: Signal model instance
        strategy_metadata: Dict from strategy detector containing:
            - smc_data: SMC-specific data (OBs, FVGs, swings, etc.)
            - extra: Additional detector-specific data
            
    Returns:
        Dict with visual elements: {
            'boxes': [...],      # Rectangles (OBs, FVGs, zones)
            'lines': [...],      # Horizontal lines (SL, TP, levels)
            'markers': [...],    # Point markers (entry, swing points)
            'labels': [...],     # Text labels
            'arrows': [...],     # Direction arrows
        }
    """
    visuals = {
        'boxes': [],
        'lines': [],
        'markers': [],
        'labels': [],
        'arrows': [],
    }
    
    try:
        # Extract signal details
        symbol = signal_obj.symbol
        side = signal_obj.side
        entry_price = float(signal_obj.price) if signal_obj.price else None
        sl_price = float(signal_obj.sl) if signal_obj.sl else None
        tp_price = float(signal_obj.tp) if signal_obj.tp else None
        timestamp = signal_obj.timestamp or datetime.now()
        
        # 1. ENTRY MARKER
        if entry_price:
            visuals['markers'].append({
                'type': 'entry',
                'time': timestamp.isoformat(),
                'price': entry_price,
                'side': side,
                'color': '#00ff00' if side == 'BUY' else '#ff0000',
                'shape': 'arrow_up' if side == 'BUY' else 'arrow_down',
                'text': f"{side} @ {entry_price:.5f}",
            })
        
        # 2. STOP LOSS LINE
        if sl_price:
            visuals['lines'].append({
                'type': 'stop_loss',
                'price': sl_price,
                'color': '#ff4444',
                'width': 2,
                'style': 'dashed',
                'text': f"SL: {sl_price:.5f}",
            })
        
        # 3. TAKE PROFIT LINE
        if tp_price:
            visuals['lines'].append({
                'type': 'take_profit',
                'price': tp_price,
                'color': '#44ff44',
                'width': 2,
                'style': 'dashed',
                'text': f"TP: {tp_price:.5f}",
            })
        
        # 4. DIRECTION ARROW
        if entry_price:
            visuals['arrows'].append({
                'type': 'direction',
                'time': timestamp.isoformat(),
                'price': entry_price,
                'direction': 'up' if side == 'BUY' else 'down',
                'color': '#00ff00' if side == 'BUY' else '#ff0000',
                'size': 'large',
            })
        
        # 5. STRATEGY-SPECIFIC VISUALS
        strategy_name = strategy_metadata.get('strategy', '')
        
        if strategy_name == 'SMC':
            _add_smc_visuals(visuals, strategy_metadata, entry_price)
        elif strategy_name == 'ICT':
            _add_ict_visuals(visuals, strategy_metadata, entry_price)
        elif strategy_name == 'SupplyDemand':
            _add_supply_demand_visuals(visuals, strategy_metadata, entry_price)
        elif strategy_name == 'Breakout':
            _add_breakout_visuals(visuals, strategy_metadata, entry_price)
        elif strategy_name == 'VWAP':
            _add_vwap_visuals(visuals, strategy_metadata, entry_price)
        
        # 6. STRUCTURE TAGS LABELS
        structure_tags = strategy_metadata.get('structure_tags', [])
        if structure_tags and entry_price:
            visuals['labels'].append({
                'type': 'structure',
                'time': timestamp.isoformat(),
                'price': entry_price * 1.001,  # Slightly above entry
                'text': ' + '.join(structure_tags),
                'color': '#ffaa00',
                'background': '#000000aa',
                'font_size': 10,
            })
        
        # 7. ENTRY REASON LABEL
        entry_reason = strategy_metadata.get('entry_reason', '')
        if entry_reason and entry_price:
            visuals['labels'].append({
                'type': 'reason',
                'time': timestamp.isoformat(),
                'price': entry_price * 0.999,  # Slightly below entry
                'text': entry_reason[:50],  # Truncate long reasons
                'color': '#ffffff',
                'background': '#333333cc',
                'font_size': 9,
            })
        
        logger.info(f"Generated visuals for signal {signal_obj.id} ({strategy_name}): "
                   f"{len(visuals['boxes'])} boxes, {len(visuals['markers'])} markers")
        
        return visuals
        
    except Exception as e:
        logger.error(f"Failed to generate visuals for signal {signal_obj.id}: {e}", 
                    exc_info=True)
        return visuals  # Return what we have so far


def _add_smc_visuals(visuals: Dict, metadata: Dict, entry_price: Optional[float]):
    """Add SMC-specific visual elements (OBs, FVGs, swings)."""
    extra = metadata.get('extra', {})
    
    # Order Blocks
    order_blocks = extra.get('order_blocks', [])
    for ob in order_blocks:
        visuals['boxes'].append({
            'type': 'order_block',
            'time_start': ob.get('start_time'),
            'time_end': ob.get('end_time'),
            'price_top': ob.get('high'),
            'price_bottom': ob.get('low'),
            'color': '#0088ff55' if ob.get('ob_type') == 'bullish' else '#ff880055',
            'border_color': '#0088ff' if ob.get('ob_type') == 'bullish' else '#ff8800',
            'border_width': 2,
            'text': f"OB ({ob.get('strength', 0):.0f}%)",
        })
    
    # Fair Value Gaps
    fvgs = extra.get('fvgs', [])
    for fvg in fvgs:
        visuals['boxes'].append({
            'type': 'fvg',
            'time_start': fvg.get('start_time'),
            'time_end': fvg.get('end_time'),
            'price_top': fvg.get('top'),
            'price_bottom': fvg.get('bottom'),
            'color': '#ffff0033',
            'border_color': '#ffff00',
            'border_width': 1,
            'style': 'dotted',
            'text': 'FVG',
        })
    
    # Swing Points
    swing_points = extra.get('swing_points', [])
    for swing in swing_points:
        visuals['markers'].append({
            'type': 'swing',
            'time': swing.get('timestamp'),
            'price': swing.get('price'),
            'swing_type': swing.get('type'),  # 'high' or 'low'
            'color': '#ff00ff' if swing.get('type') == 'high' else '#00ffff',
            'shape': 'triangle',
            'size': 'small',
        })
    
    # Liquidity Levels
    liquidity_levels = extra.get('liquidity_levels', [])
    for level in liquidity_levels:
        visuals['lines'].append({
            'type': 'liquidity',
            'price': level.get('price'),
            'color': '#ff00ff',
            'width': 1,
            'style': 'dotted',
            'text': f"Liquidity ({level.get('type', 'unknown')})",
        })


def _add_ict_visuals(visuals: Dict, metadata: Dict, entry_price: Optional[float]):
    """Add ICT-specific visual elements (killzones, FVGs)."""
    extra = metadata.get('extra', {})
    
    # Killzone highlight
    killzone = extra.get('killzone')
    if killzone:
        visuals['labels'].append({
            'type': 'killzone',
            'time': extra.get('timestamp'),
            'price': entry_price * 1.002 if entry_price else 0,
            'text': f"🎯 {killzone.upper()} Killzone",
            'color': '#ffff00',
            'background': '#00000088',
            'font_size': 11,
            'font_weight': 'bold',
        })
    
    # Wick rejection zone
    rejection_zone = extra.get('rejection_zone')
    if rejection_zone:
        visuals['boxes'].append({
            'type': 'rejection_zone',
            'time_start': rejection_zone.get('start_time'),
            'time_end': rejection_zone.get('end_time'),
            'price_top': rejection_zone.get('high'),
            'price_bottom': rejection_zone.get('low'),
            'color': '#ff990033',
            'border_color': '#ff9900',
            'border_width': 2,
            'text': 'Wick Rejection',
        })
    
    # Fair Value Gaps (ICT style)
    fvgs = extra.get('fvgs', [])
    for fvg in fvgs:
        visuals['boxes'].append({
            'type': 'fvg_ict',
            'time_start': fvg.get('start_time'),
            'time_end': fvg.get('end_time'),
            'price_top': fvg.get('top'),
            'price_bottom': fvg.get('bottom'),
            'color': '#00ffff22',
            'border_color': '#00ffff',
            'border_width': 1,
            'text': 'FVG',
        })


def _add_supply_demand_visuals(visuals: Dict, metadata: Dict, entry_price: Optional[float]):
    """Add Supply/Demand zone visual elements."""
    extra = metadata.get('extra', {})
    
    # Supply zones
    supply_zones = extra.get('supply_zones', [])
    for zone in supply_zones:
        visuals['boxes'].append({
            'type': 'supply_zone',
            'time_start': zone.get('start_time'),
            'time_end': zone.get('end_time'),
            'price_top': zone.get('top'),
            'price_bottom': zone.get('bottom'),
            'color': '#ff000033',
            'border_color': '#ff0000',
            'border_width': 2,
            'text': f"Supply ({zone.get('strength', 0):.0f}%)",
        })
    
    # Demand zones
    demand_zones = extra.get('demand_zones', [])
    for zone in demand_zones:
        visuals['boxes'].append({
            'type': 'demand_zone',
            'time_start': zone.get('start_time'),
            'time_end': zone.get('end_time'),
            'price_top': zone.get('top'),
            'price_bottom': zone.get('bottom'),
            'color': '#00ff0033',
            'border_color': '#00ff00',
            'border_width': 2,
            'text': f"Demand ({zone.get('strength', 0):.0f}%)",
        })
    
    # Displacement candle
    displacement = extra.get('displacement_candle')
    if displacement:
        visuals['markers'].append({
            'type': 'displacement',
            'time': displacement.get('timestamp'),
            'price': displacement.get('close'),
            'color': '#ffff00',
            'shape': 'star',
            'size': 'medium',
            'text': 'Displacement',
        })


def _add_breakout_visuals(visuals: Dict, metadata: Dict, entry_price: Optional[float]):
    """Add Breakout-specific visual elements (channels, breakout points)."""
    extra = metadata.get('extra', {})
    
    # Donchian channel upper
    upper_channel = extra.get('upper_channel')
    if upper_channel:
        visuals['lines'].append({
            'type': 'channel_upper',
            'price': upper_channel,
            'color': '#ff6600',
            'width': 2,
            'style': 'solid',
            'text': 'Upper Channel',
        })
    
    # Donchian channel lower
    lower_channel = extra.get('lower_channel')
    if lower_channel:
        visuals['lines'].append({
            'type': 'channel_lower',
            'price': lower_channel,
            'color': '#0066ff',
            'width': 2,
            'style': 'solid',
            'text': 'Lower Channel',
        })
    
    # Breakout point marker
    breakout_price = extra.get('breakout_price')
    breakout_time = extra.get('breakout_time')
    if breakout_price and breakout_time:
        visuals['markers'].append({
            'type': 'breakout',
            'time': breakout_time,
            'price': breakout_price,
            'color': '#ff00ff',
            'shape': 'diamond',
            'size': 'large',
            'text': 'BREAKOUT!',
        })


def _add_vwap_visuals(visuals: Dict, metadata: Dict, entry_price: Optional[float]):
    """Add VWAP-specific visual elements."""
    extra = metadata.get('extra', {})
    
    # VWAP line
    vwap_price = extra.get('vwap_price')
    if vwap_price:
        visuals['lines'].append({
            'type': 'vwap',
            'price': vwap_price,
            'color': '#9966ff',
            'width': 3,
            'style': 'solid',
            'text': f"VWAP: {vwap_price:.5f}",
        })
    
    # VWAP cross marker
    cross_type = extra.get('cross_type')  # 'reclaim' or 'breakdown'
    if cross_type and entry_price:
        visuals['markers'].append({
            'type': 'vwap_cross',
            'time': extra.get('timestamp'),
            'price': vwap_price,
            'color': '#00ff00' if cross_type == 'reclaim' else '#ff0000',
            'shape': 'circle',
            'size': 'large',
            'text': f"VWAP {cross_type.upper()}",
        })


def generate_backtest_visuals(trades: List[Dict]) -> Dict:
    """
    Generate visuals for a complete backtest run.
    
    Args:
        trades: List of trade dicts from BacktestTrade model
        
    Returns:
        Dict with visual elements for all trades
    """
    visuals = {
        'trades': [],
        'equity_curve': [],
        'drawdown_zones': [],
        'statistics': {},
    }
    
    try:
        # Process each trade
        for trade in trades:
            trade_visual = {
                'entry_time': trade.get('entry_time'),
                'entry_price': trade.get('entry_price'),
                'exit_time': trade.get('exit_time'),
                'exit_price': trade.get('exit_price'),
                'side': trade.get('side'),
                'pnl': trade.get('pnl'),
                'color': '#00ff00' if trade.get('pnl', 0) > 0 else '#ff0000',
            }
            visuals['trades'].append(trade_visual)
        
        # Calculate equity curve
        equity = 10000  # Starting balance
        for i, trade in enumerate(trades):
            pnl = trade.get('pnl', 0)
            equity += pnl
            
            visuals['equity_curve'].append({
                'time': trade.get('exit_time'),
                'equity': equity,
                'trade_number': i + 1,
            })
        
        # Identify drawdown zones
        peak_equity = 10000
        in_drawdown = False
        dd_start = None
        
        for point in visuals['equity_curve']:
            equity = point['equity']
            
            if equity > peak_equity:
                # New peak - end any drawdown
                if in_drawdown and dd_start:
                    visuals['drawdown_zones'].append({
                        'start_time': dd_start['time'],
                        'end_time': point['time'],
                        'start_equity': dd_start['equity'],
                        'bottom_equity': min_equity,
                        'drawdown_pct': ((peak_equity - min_equity) / peak_equity) * 100,
                    })
                    in_drawdown = False
                
                peak_equity = equity
            else:
                # In drawdown
                if not in_drawdown:
                    in_drawdown = True
                    dd_start = point
                    min_equity = equity
                else:
                    min_equity = min(min_equity, equity)
        
        # Add statistics
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t.get('pnl', 0) > 0)
        losing_trades = total_trades - winning_trades
        
        visuals['statistics'] = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            'final_equity': equity,
            'total_return': ((equity - 10000) / 10000) * 100,
            'drawdown_count': len(visuals['drawdown_zones']),
        }
        
        logger.info(f"Generated backtest visuals: {total_trades} trades, "
                   f"{winning_trades}W/{losing_trades}L")
        
        return visuals
        
    except Exception as e:
        logger.error(f"Failed to generate backtest visuals: {e}", exc_info=True)
        return visuals


def export_to_tradingview_format(visuals: Dict) -> str:
    """
    Export visuals to TradingView Pine Script format.
    
    Args:
        visuals: Visuals dict from generate_signal_visuals()
        
    Returns:
        Pine Script code snippet
    """
    pine_code = "// Auto-generated by ZenithEdge Engine\n\n"
    
    # Boxes
    for box in visuals.get('boxes', []):
        pine_code += (
            f"box.new(left={box['time_start']}, top={box['price_top']}, "
            f"right={box['time_end']}, bottom={box['price_bottom']}, "
            f"border_color=color.{box['border_color']}, bgcolor=color.{box['color']}, "
            f"text=\"{box['text']}\")\n"
        )
    
    # Lines
    for line in visuals.get('lines', []):
        pine_code += (
            f"hline({line['price']}, title=\"{line['text']}\", "
            f"color=color.{line['color']}, linestyle=line.style_{line['style']})\n"
        )
    
    # Markers
    for marker in visuals.get('markers', []):
        shape = marker['shape'].upper()
        pine_code += (
            f"plotshape(series={marker['price']}, style=shape.{shape}, "
            f"location=location.absolute, color=color.{marker['color']}, "
            f"text=\"{marker['text']}\")\n"
        )
    
    return pine_code


def export_to_json(visuals: Dict) -> Dict:
    """
    Export visuals to JSON format (for REST API).
    
    Args:
        visuals: Visuals dict
        
    Returns:
        JSON-serializable dict
    """
    # Already in JSON-compatible format
    return {
        'boxes': visuals.get('boxes', []),
        'lines': visuals.get('lines', []),
        'markers': visuals.get('markers', []),
        'labels': visuals.get('labels', []),
        'arrows': visuals.get('arrows', []),
        'version': '1.0',
        'generator': 'zenithedge_engine',
    }


# Convenience function for testing
def test_visuals():
    """Test the visuals module with synthetic data."""
    print("🎨 Testing Engine Visuals Module\n")
    
    # Mock signal object
    class MockSignal:
        def __init__(self):
            self.id = 1
            self.symbol = 'EURUSD'
            self.side = 'BUY'
            self.price = Decimal('1.1000')
            self.sl = Decimal('1.0950')
            self.tp = Decimal('1.1100')
            self.timestamp = datetime.now()
    
    signal = MockSignal()
    
    # Mock strategy metadata
    metadata = {
        'strategy': 'SMC',
        'confidence': 82,
        'regime': 'Trending',
        'entry_reason': 'BOS + OB retest in discount zone',
        'structure_tags': ['BOS', 'OB_retest', 'discount'],
        'extra': {
            'order_blocks': [
                {
                    'start_time': '2024-01-01T10:00:00',
                    'end_time': '2024-01-01T12:00:00',
                    'high': 1.0980,
                    'low': 1.0960,
                    'ob_type': 'bullish',
                    'strength': 78,
                }
            ],
            'fvgs': [
                {
                    'start_time': '2024-01-01T11:00:00',
                    'end_time': '2024-01-01T11:30:00',
                    'top': 1.0990,
                    'bottom': 1.0985,
                }
            ],
        }
    }
    
    # Generate visuals
    visuals = generate_signal_visuals(signal, metadata)
    
    print(f"Generated visuals:")
    print(f"  - Boxes: {len(visuals['boxes'])}")
    print(f"  - Lines: {len(visuals['lines'])}")
    print(f"  - Markers: {len(visuals['markers'])}")
    print(f"  - Labels: {len(visuals['labels'])}")
    print(f"  - Arrows: {len(visuals['arrows'])}\n")
    
    # Export to JSON
    json_output = export_to_json(visuals)
    print(f"JSON export: {len(str(json_output))} characters\n")
    
    print("✅ Visuals module test complete!")


if __name__ == '__main__':
    test_visuals()
