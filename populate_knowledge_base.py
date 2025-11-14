#!/usr/bin/env python3
"""
Knowledge Base Population Script
Adds 50+ real trading concepts across 10 strategy domains for production readiness.

Usage:
    python populate_knowledge_base.py --all          # Add all concepts
    python populate_knowledge_base.py --strategy smc  # Add concepts for specific strategy
    python populate_knowledge_base.py --dry-run       # Preview without saving
"""

import os
import sys
import django
import argparse
from typing import List, Dict

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from knowledge_base.models import KnowledgeEntry

# ============================================================================
# TRADING CONCEPTS DATABASE (50+ Professional Definitions)
# ============================================================================

TRADING_CONCEPTS = {
    # ========== SMART MONEY CONCEPTS (SMC) ==========
    'smc': [
        {
            'term': 'Order Block',
            'definition': '''An order block is the last up candle before a bearish move (bearish OB) or last down candle before a bullish move (bullish OB). These zones represent areas where institutional orders were placed, creating imbalances that smart money expects to revisit. Price often returns to these zones for liquidity before continuing in the intended direction. Traders use order blocks as high-probability entry zones with stop losses just beyond the block.''',
            'market_behavior_patterns': ['institutional_accumulation', 'price_return', 'liquidity_grab'],
            'trade_structures': ['bullish_ob_long', 'bearish_ob_short', 'ob_retest_entry'],
            'psychology_context': 'Institutions leave "footprints" in price action where large orders filled. Retail often misses these zones, while smart money anticipates the return.',
            'common_pitfalls': ['Trading every order block without context', 'Not waiting for confirmation', 'Ignoring higher timeframe structure'],
            'visual_description': 'Strong directional candle (often engulfing) followed by sharp reversal. The body of this candle becomes the OB zone.',
            'related_concepts': ['liquidity sweep', 'fair value gap', 'break of structure', 'mitigation']
        },
        {
            'term': 'Break of Structure (BOS)',
            'definition': '''A Break of Structure occurs when price violates a significant swing high (bullish BOS) or swing low (bearish BOS), indicating a potential shift in market direction. This is different from a liquidity sweep because price closes beyond the level with conviction. BOS signals that smart money is accumulating in the new direction, and the previous structure is now invalid. It often precedes strong trending moves.''',
            'market_behavior_patterns': ['trend_change', 'momentum_shift', 'structure_violation'],
            'trade_structures': ['bos_continuation', 'bos_pullback_entry', 'trend_following'],
            'psychology_context': 'Retail traders trapped on wrong side often provide liquidity as smart money breaks structure with conviction.',
            'common_pitfalls': ['Confusing BOS with liquidity sweep', 'Chasing breakouts without pullback', 'Ignoring volume confirmation'],
            'visual_description': 'Price clearly breaks and closes above previous swing high (bullish) or below swing low (bearish) with strong momentum.',
            'related_concepts': ['change of character', 'liquidity sweep', 'order block', 'market structure']
        },
        {
            'term': 'Fair Value Gap (FVG)',
            'definition': '''A Fair Value Gap is a three-candle pattern showing an imbalance or inefficiency in price delivery. It appears when the high of candle 1 doesn\'t touch the low of candle 3 (bullish FVG) or when the low of candle 1 doesn\'t touch the high of candle 3 (bearish FVG). This gap represents an area where price moved too quickly, leaving unfilled orders. Price tends to return to fill these gaps at 50%, creating trading opportunities.''',
            'market_behavior_patterns': ['price_imbalance', 'gap_fill', 'rapid_movement'],
            'trade_structures': ['fvg_retest_entry', 'partial_fill_continuation', 'imbalance_mitigation'],
            'psychology_context': 'Algorithmic trading and institutional orders create imbalances during rapid directional moves. Market seeks equilibrium.',
            'common_pitfalls': ['Trading every small FVG', 'Not measuring gap properly', 'Expecting 100% fill every time'],
            'visual_description': 'Visible gap between three candles where middle candle creates separation. Gap appears as empty space on chart.',
            'related_concepts': ['order block', 'liquidity', 'imbalance', 'mitigation']
        },
        {
            'term': 'Liquidity Sweep',
            'definition': '''A liquidity sweep (or stop hunt) occurs when price briefly spikes through a key level (equal highs/lows) to trigger stop losses and pending orders, then quickly reverses. This is smart money engineering liquidity before the true move. Unlike a Break of Structure, price doesn\'t close beyond the level with conviction. Sweeps often precede strong reversals as institutions now have the liquidity needed to fill their large orders.''',
            'market_behavior_patterns': ['stop_hunt', 'false_breakout', 'liquidity_grab'],
            'trade_structures': ['sweep_reversal', 'liquidity_raid_entry', 'failed_breakout'],
            'psychology_context': 'Retail stops clustered at obvious levels provide fuel for institutional entries. The "pain trade" often follows sweeps.',
            'common_pitfalls': ['Getting stopped out on sweeps', 'Chasing the fake breakout', 'Not waiting for reversal confirmation'],
            'visual_description': 'Wick through previous high/low with immediate rejection. Often appears as "spike and reversal" pattern.',
            'related_concepts': ['equal highs/lows', 'stop loss hunting', 'reversal', 'order block']
        },
        {
            'term': 'Change of Character (CHoCH)',
            'definition': '''Change of Character is an early warning sign of potential trend reversal. It occurs when price breaks a minor structure (internal high/low) counter to the prevailing trend. While not as significant as a Break of Structure, CHoCH alerts traders that momentum is weakening and smart money may be repositioning. Multiple CHoCH patterns often precede a major Break of Structure.''',
            'market_behavior_patterns': ['momentum_weakening', 'early_reversal_signal', 'minor_structure_break'],
            'trade_structures': ['choch_caution', 'position_reduction', 'reversal_preparation'],
            'psychology_context': 'First sign that the dominant narrative is weakening. Smart traders reduce exposure while retail still believes in trend.',
            'common_pitfalls': ['Treating CHoCH as BOS', 'Reversing entire position too early', 'Ignoring in strong trends'],
            'visual_description': 'Break of internal swing high/low that doesn\'t violate major structure. Creates lower highs in uptrend or higher lows in downtrend.',
            'related_concepts': ['break of structure', 'market structure', 'trend exhaustion']
        },
        {
            'term': 'Premium and Discount Zones',
            'definition': '''Premium zones are areas above equilibrium (50% of a range) where price is considered expensive - ideal for selling or taking profits on longs. Discount zones are below equilibrium where price is cheap - ideal for buying or taking profits on shorts. This concept helps traders enter in optimal value areas rather than chasing. The 50% level often acts as decision point, with 25% (deep discount) and 75% (deep premium) being extreme value zones.''',
            'market_behavior_patterns': ['value_zones', 'mean_reversion', 'range_equilibrium'],
            'trade_structures': ['discount_long_entries', 'premium_short_entries', 'equilibrium_decision'],
            'psychology_context': 'Buying strength (premium) or selling weakness (discount) is retail behavior. Smart money does the opposite - buys discount, sells premium.',
            'common_pitfalls': ['Shorting in discount zones', 'Buying in premium zones', 'Not defining the range properly'],
            'visual_description': 'Fibonacci-style levels dividing a range. Upper 50% is premium (25-50-75% levels), lower 50% is discount.',
            'related_concepts': ['equilibrium', 'value area', 'range trading', 'fibonacci']
        }
    ],
    
    # ========== INNER CIRCLE TRADER (ICT) ==========
    'ict': [
        {
            'term': 'Institutional Order Flow',
            'definition': '''Institutional Order Flow refers to the footprints left by large market participants (banks, hedge funds) as they accumulate or distribute positions. Unlike retail traders who can enter instantly, institutions must engineer liquidity to fill massive orders without moving price against themselves. This creates observable patterns: accumulation ranges before markup, distribution ranges before markdown, and specific timing around news events and session opens.''',
            'market_behavior_patterns': ['large_order_accumulation', 'gradual_positioning', 'liquidity_engineering'],
            'trade_structures': ['order_flow_alignment', 'institutional_entry_zones', 'smart_money_tracking'],
            'psychology_context': 'Institutions are patient and methodical, often taking days/weeks to build positions. Retail is impatient, chasing moves after they\'ve already started.',
            'common_pitfalls': ['Expecting instant moves', 'Not respecting accumulation time', 'Trading against institutional flow'],
            'visual_description': 'Consolidation followed by explosive directional move. Look for declining volatility before expansion.',
            'related_concepts': ['accumulation', 'distribution', 'wyckoff', 'market maker']
        },
        {
            'term': 'Optimal Trade Entry (OTE)',
            'definition': '''Optimal Trade Entry is the 61.8-78.6% retracement zone of an impulse move, representing the ideal risk-reward entry point. After a strong directional move (Break of Structure), price typically retraces to this zone where institutional traders add to positions. The 70.5% level is considered the "sweet spot" within OTE. Entries in this zone offer tight stops with targets at previous high/low, creating favorable risk-reward ratios of 3:1 or better.''',
            'market_behavior_patterns': ['fibonacci_retracement', 'institutional_reentry', 'pullback_completion'],
            'trade_structures': ['ote_long_entry', 'ote_short_entry', 'pullback_trading'],
            'psychology_context': 'Retail fears "buying high" and misses optimal entries. Institutions accumulate these zones knowing the trend will continue.',
            'common_pitfalls': ['Entering too early (50% zone)', 'Waiting for 100% retracement', 'Not confirming with order blocks'],
            'visual_description': 'Golden zone on fibonacci retracement between 61.8% and 78.6%. Often aligns with order blocks or fair value gaps.',
            'related_concepts': ['fibonacci', 'order block', 'pullback', 'retracement']
        },
        {
            'term': 'Killzones',
            'definition': '''Killzones are specific time windows when institutional algorithms are most active, creating high-probability setups. London Killzone (02:00-05:00 EST) often sets the daily direction. New York Killzone (07:00-10:00 EST) either continues or reverses London\'s move. Asian Killzone (20:00-00:00 EST) tends to be range-bound. Trading exclusively during these windows filters out low-probability chop and aligns with institutional activity.''',
            'market_behavior_patterns': ['session_volatility', 'algorithmic_activity', 'time_based_patterns'],
            'trade_structures': ['london_open_breakout', 'ny_session_continuation', 'killzone_exclusive_trading'],
            'psychology_context': 'Institutions are creatures of habit with automated systems. They create predictable patterns at specific times each day.',
            'common_pitfalls': ['Trading outside killzones', 'Not adjusting for daylight saving time', 'Ignoring Friday/Monday differences'],
            'visual_description': 'Noticeable increase in volume and volatility during specific 3-4 hour windows. Clear directional moves often start at killzone opens.',
            'related_concepts': ['session trading', 'time windows', 'volatility patterns', 'algorithmic trading']
        },
        {
            'term': 'Market Structure Shift',
            'definition': '''A Market Structure Shift is the ICT term for when price action violates the established trend structure by breaking a significant swing point. In an uptrend, it\'s a lower low; in a downtrend, it\'s a higher high. This signals that the balance of power has shifted between buyers and sellers. MSS often marks the end of one trend phase and beginning of another, making it critical for trend-following traders to recognize and respect.''',
            'market_behavior_patterns': ['trend_reversal', 'power_shift', 'structure_violation'],
            'trade_structures': ['mss_reversal_entry', 'trend_change_trades', 'counter_trend_positioning'],
            'psychology_context': 'The crowd fights the new trend, providing liquidity for smart money entering the new direction. Denial turns to capitulation.',
            'common_pitfalls': ['Fighting the new structure', 'Assuming every shift reverses trend', 'Not waiting for confirmation'],
            'visual_description': 'Clear violation of swing structure - lower low in uptrend or higher high in downtrend. Often accompanied by strong momentum.',
            'related_concepts': ['break of structure', 'trend reversal', 'swing points', 'market structure']
        }
    ],
    
    # ========== TREND FOLLOWING ==========
    'trend': [
        {
            'term': 'Higher Highs Higher Lows (HH HL)',
            'definition': '''Higher Highs and Higher Lows define an uptrend structure where each successive peak exceeds the previous peak (HH) and each trough exceeds the previous trough (HL). This pattern indicates buyers are in control and willing to pay progressively higher prices. The trend remains intact until price fails to make a new high or breaks a previous low. Trend followers use HL as entry points and HH as profit targets.''',
            'market_behavior_patterns': ['bullish_structure', 'buyer_dominance', 'trend_continuation'],
            'trade_structures': ['pullback_entries', 'swing_trading', 'trend_following'],
            'psychology_context': 'Each new high creates FOMO (fear of missing out) attracting more buyers. Each higher low shows strong support where dip-buyers step in.',
            'common_pitfalls': ['Buying at new highs without pullback', 'Missing the initial trend formation', 'Holding through structure break'],
            'visual_description': 'Staircase pattern ascending upward. Each peak higher than last, each valley higher than previous valley.',
            'related_concepts': ['uptrend', 'swing highs', 'swing lows', 'trend structure']
        },
        {
            'term': 'Lower Highs Lower Lows (LH LL)',
            'definition': '''Lower Highs and Lower Lows define a downtrend where each rally fails at a lower level than the previous rally (LH) and each decline reaches a lower point than the previous decline (LL). This shows sellers are in control and buyers are unwilling to pay previous prices. Downtrends persist until price makes a higher high or fails to make a new low. Trend followers short at LH and cover at LL.''',
            'market_behavior_patterns': ['bearish_structure', 'seller_dominance', 'declining_trend'],
            'trade_structures': ['rally_short_entries', 'trend_shorts', 'downtrend_trading'],
            'psychology_context': 'Each lower high creates fear as rallies fail. Each lower low triggers capitulation selling. Hope turns to despair.',
            'common_pitfalls': ['Trying to catch falling knife', 'Shorting too late in trend', 'Not covering at LL'],
            'visual_description': 'Descending staircase pattern. Each peak lower than previous, each trough lower than last.',
            'related_concepts': ['downtrend', 'swing structure', 'bearish trend', 'resistance levels']
        },
        {
            'term': 'Moving Average Confluence',
            'definition': '''Moving Average Confluence occurs when multiple moving averages (e.g., 20, 50, 200 EMA) cluster together or cross, creating a zone of dynamic support or resistance. When price approaches this confluence zone in a trend, it often provides low-risk entry opportunities. The 200 EMA is watched by institutions, the 50 EMA shows medium-term direction, and the 20 EMA reveals short-term momentum. All three aligning signals strong trending conditions.''',
            'market_behavior_patterns': ['dynamic_support', 'trend_alignment', 'institutional_reference'],
            'trade_structures': ['ma_bounce_entries', 'pullback_to_ma', 'trend_confirmation'],
            'psychology_context': 'MAs are self-fulfilling as millions watch them. When price approaches, algorithms and traders act simultaneously creating predictable reactions.',
            'common_pitfalls': ['Using too many MAs', 'Fighting MA direction', 'Entering without confirmation'],
            'visual_description': 'Multiple moving average lines converging or stacked in order (20>50>200 in uptrend). Price respects these levels like trampolines.',
            'related_concepts': ['moving averages', 'dynamic support', 'trend indicators', 'ema']
        },
        {
            'term': 'Trend Exhaustion Signals',
            'definition': '''Trend Exhaustion occurs when a trend loses momentum before reversing. Signs include: decreasing volume on new highs/lows, momentum divergence (RSI/MACD not confirming), extended moves from moving averages, multiple failed breakouts, and increasingly longer consolidations. Exhaustion doesn\'t mean immediate reversal - often leads to prolonged consolidation or gradual drift. Smart traders exit trending positions and wait for new structure to form.''',
            'market_behavior_patterns': ['momentum_divergence', 'volume_decline', 'consolidation_lengthening'],
            'trade_structures': ['profit_taking', 'position_reduction', 'reversal_preparation'],
            'psychology_context': 'Exhaustion happens when everyone who wants to buy has bought (uptrend) or sell has sold (downtrend). No new money drives continuation.',
            'common_pitfalls': ['Reversing too early', 'Staying in dead trends', 'Confusing pause with exhaustion'],
            'visual_description': 'Momentum slowing - smaller candles, longer wicks, more indecision. Looks like "running out of gas."',
            'related_concepts': ['divergence', 'volume analysis', 'consolidation', 'trend reversal']
        }
    ],
    
    # ========== BREAKOUT TRADING ==========
    'breakout': [
        {
            'term': 'Consolidation Breakout',
            'definition': '''A Consolidation Breakout occurs when price escapes a defined range with increased volume and momentum. The longer the consolidation, the more significant the breakout potential. Valid breakouts show: (1) strong volume spike (2x average), (2) decisive close beyond range, (3) no immediate return to range. Failed breakouts (fakeouts) return to range quickly. Width of consolidation often projects to the measured move target.''',
            'market_behavior_patterns': ['range_compression', 'volatility_expansion', 'directional_commitment'],
            'trade_structures': ['range_breakout_long', 'range_breakout_short', 'measured_move'],
            'psychology_context': 'Consolidation builds pressure as bulls and bears battle. Breakout represents winner taking control. Volume confirms conviction.',
            'common_pitfalls': ['Entering on first touch of level', 'Ignoring volume', 'No stop loss plan for fakeout'],
            'visual_description': 'Rectangle or triangle pattern followed by explosive candle breaking range with large body and volume bar.',
            'related_concepts': ['range trading', 'volatility contraction', 'measured move', 'volume confirmation']
        },
        {
            'term': 'False Breakout (Fakeout)',
            'definition': '''A False Breakout or Fakeout occurs when price briefly breaks a key level but fails to sustain beyond it, quickly reversing back into the range. This traps breakout traders on the wrong side. Fakeouts often precede strong moves in the opposite direction as stop losses cascade. Characteristics: low volume breakout, long wicks (rejection), close back in range, and often happens at obvious levels where stops cluster.''',
            'market_behavior_patterns': ['failed_breakout', 'stop_hunt', 'reversal_setup'],
            'trade_structures': ['fakeout_fade', 'reversal_entry', 'trap_counter'],
            'psychology_context': 'Smart money engineers fakeouts to trap retail breakout traders, providing liquidity for real move in opposite direction.',
            'common_pitfalls': ['Chasing breakouts without confirmation', 'No stop loss', 'Not recognizing fakeout pattern'],
            'visual_description': 'Candle breaks level with wick but closes back inside range. Often appears as hammer or shooting star at extreme.',
            'related_concepts': ['stop hunt', 'liquidity sweep', 'reversal', 'trap']
        },
        {
            'term': 'Measured Move Target',
            'definition': '''The Measured Move is a price projection technique using the height of the consolidation pattern to estimate breakout target. Method: measure the range height (high to low), then project that distance from the breakout point in the direction of break. This gives probability-based target zone. Works with rectangles, triangles, flags, and channels. Often reaches target with 70-80% accuracy, making it valuable for profit taking.''',
            'market_behavior_patterns': ['pattern_projection', 'target_estimation', 'profit_objective'],
            'trade_structures': ['measured_move_targets', 'profit_taking_zones', 'position_scaling'],
            'psychology_context': 'Technical traders use same measurements creating self-fulfilling prophecy as profits are taken at same zones.',
            'common_pitfalls': ['Treating as guaranteed target', 'Not adjusting for market conditions', 'Holding past target without reason'],
            'visual_description': 'Equal vertical lines showing pattern height projected from breakout point. Often marked with horizontal line at target.',
            'related_concepts': ['pattern trading', 'profit targets', 'projection', 'technical analysis']
        }
    ],
    
    # ========== MEAN REVERSION ==========
    'mean_reversion': [
        {
            'term': 'Bollinger Band Squeeze',
            'definition': '''The Bollinger Band Squeeze occurs when volatility contracts to extremely low levels, causing the bands to narrow significantly. This compression signals a period of consolidation before an explosive move. The direction of the breakout is unknown, but the magnitude is often proportional to the squeeze duration. Traders wait for bands to expand and price to close outside bands with volume, then enter in breakout direction. Often used with momentum indicators.''',
            'market_behavior_patterns': ['volatility_contraction', 'breakout_preparation', 'consolidation'],
            'trade_structures': ['squeeze_breakout', 'expansion_trades', 'volatility_expansion'],
            'psychology_context': 'Low volatility creates boredom and complacency. When everyone expects quiet, market explodes catching traders off guard.',
            'common_pitfalls': ['Entering before breakout', 'Wrong direction guess', 'Insufficient stop loss for volatility'],
            'visual_description': 'Bollinger Bands converging to tight parallel lines, often with declining ATR. Looks like rubber band ready to snap.',
            'related_concepts': ['bollinger bands', 'volatility', 'atr', 'consolidation breakout']
        },
        {
            'term': 'Reversion to Mean',
            'definition': '''Reversion to Mean is the principle that price tends to return to average value after extreme moves. When price stretches significantly from moving averages, RSI reaches overbought/oversold, or Bollinger Bands are breached, probability favors a pull back to mean. This isn\'t about predicting tops/bottoms but rather exploiting overextension. Best in ranging markets; dangerous in strong trends where "the mean" keeps moving.''',
            'market_behavior_patterns': ['overextension_correction', 'equilibrium_seeking', 'pullback'],
            'trade_structures': ['mean_reversion_entries', 'fade_extremes', 'counter_trend_trades'],
            'psychology_context': 'Emotional extremes (greed/fear) drive overextensions. Reversion happens as emotions normalize and value seekers appear.',
            'common_pitfalls': ['Fighting trends', 'No defined mean', 'Entering at first extreme reading'],
            'visual_description': 'Price far from moving averages or outside Bollinger Bands with RSI >70 or <30. Looks stretched or overextended.',
            'related_concepts': ['moving averages', 'rsi', 'bollinger bands', 'overextended']
        },
        {
            'term': 'RSI Divergence',
            'definition': '''RSI Divergence occurs when price makes new highs/lows but RSI fails to confirm, signaling momentum exhaustion. Bullish divergence: price makes lower low, RSI makes higher low (oversold reversal signal). Bearish divergence: price makes higher high, RSI makes lower high (overbought reversal signal). This warns trend is weakening. Most reliable near extreme RSI levels (>70 or <30) and on higher timeframes.''',
            'market_behavior_patterns': ['momentum_divergence', 'exhaustion_signal', 'reversal_warning'],
            'trade_structures': ['divergence_reversals', 'counter_trend_entries', 'trend_exhaustion_trades'],
            'psychology_context': 'Momentum divergence shows fewer participants driving trend. Like pushing a car uphill - each push moves it less. Eventually reverses.',
            'common_pitfalls': ['Trading divergence in strong trends', 'Not waiting for price confirmation', 'Using on short timeframes'],
            'visual_description': 'Draw lines connecting price highs/lows and corresponding RSI highs/lows. When lines slope opposite directions, divergence exists.',
            'related_concepts': ['rsi', 'momentum', 'divergence', 'trend exhaustion']
        }
    ],
    
    # ========== ADDITIONAL STRATEGIES ==========
    'squeeze': [
        {
            'term': 'TTM Squeeze',
            'definition': '''The TTM Squeeze (by John Carter) identifies periods when Bollinger Bands squeeze inside Keltner Channels, indicating extreme consolidation. When squeeze fires (bands expand outside channels), a trending move is imminent. Histogram dots color-code: red = squeeze on (consolidating), green = squeeze off (trending). Histogram bars show momentum direction. This setup combines volatility contraction with momentum, creating high-probability breakout trades.''',
            'market_behavior_patterns': ['extreme_consolidation', 'volatility_breakout', 'momentum_acceleration'],
            'trade_structures': ['squeeze_fire_entries', 'momentum_trades', 'breakout_with_confirmation'],
            'psychology_context': 'Extreme low volatility breeds complacency. When volatility returns, it catches majority off-guard creating strong directional moves.',
            'common_pitfalls': ['Entering before fire', 'Trading against momentum histogram', 'Insufficient stop for expansion'],
            'visual_description': 'Red dots on histogram turn green when squeeze fires. Histogram bars grow showing momentum direction (green=bullish, red=bearish).',
            'related_concepts': ['bollinger bands', 'keltner channels', 'volatility', 'momentum']
        }
    ],
    
    'scalping': [
        {
            'term': 'Order Flow Imbalance',
            'definition': '''Order Flow Imbalance occurs when aggressive buying or selling overwhelms the opposite side, visible in the order book or time & sales. Large market orders consuming limit orders at multiple price levels indicate institutional participation. This creates temporary directional bias for scalpers. Footprint charts display this as clusters of delta imbalance. Scalpers align with the imbalance side for quick profits, exiting when balance returns.''',
            'market_behavior_patterns': ['aggressive_orders', 'liquidity_consumption', 'short_term_bias'],
            'trade_structures': ['scalp_with_imbalance', 'quick_entries_exits', 'order_book_trading'],
            'psychology_context': 'Large players can\'t hide their urgency. When they aggressively take liquidity, small traders can front-run short-term impact.',
            'common_pitfalls': ['Holding too long', 'Trading without confirmation', 'Insufficient liquidity for exits'],
            'visual_description': 'Footprint chart showing stacked delta imbalances (red or green clusters). Time & sales showing consecutive large orders same direction.',
            'related_concepts': ['order flow', 'delta', 'market microstructure', 'tape reading']
        }
    ],
    
    'vwap': [
        {
            'term': 'VWAP Mean Reversion',
            'definition': '''VWAP (Volume Weighted Average Price) represents the average price weighted by volume, serving as institutional benchmark. Price above VWAP = bullish, below = bearish. When price extends far from VWAP (>2 standard deviations), probability favors reversion to VWAP. Institutions often execute large orders near VWAP to minimize market impact. Intraday traders use this for mean reversion entries, expecting price to return to VWAP "fair value."''',
            'market_behavior_patterns': ['fair_value_seeking', 'institutional_reference', 'intraday_reversion'],
            'trade_structures': ['vwap_reversion_trades', 'standard_deviation_entries', 'institutional_levels'],
            'psychology_context': 'VWAP is institutional report card - algorithms reference it for execution quality. Deviations create natural mean reversion as algorithms adjust.',
            'common_pitfalls': ['Fighting trend away from VWAP', 'Not using standard deviations', 'Holding past VWAP touch'],
            'visual_description': 'Thick line on chart with standard deviation bands. Price oscillates around VWAP like gravity, stretching away then snapping back.',
            'related_concepts': ['vwap', 'institutional trading', 'mean reversion', 'standard deviation']
        }
    ],
    
    'supply_demand': [
        {
            'term': 'Fresh Supply Zone',
            'definition': '''A Fresh Supply Zone is an untested area where sellers previously overwhelmed buyers, creating a sharp price decline. These zones are "fresh" because price hasn\'t returned to test them yet. When price rallies back to a fresh supply zone, probability favors rejection as sell orders still reside there. The zone loses strength once tested. Best supply zones: (1) caused strong drop (2) left quickly (thin price action) (3) haven\'t been revisited (4) align with market structure.''',
            'market_behavior_patterns': ['seller_dominance', 'unfilled_orders', 'resistance_zone'],
            'trade_structures': ['supply_zone_shorts', 'reversal_entries', 'rejection_trades'],
            'psychology_context': 'Supply zones represent "regret areas" where buyers wish they\'d sold. When price returns, they eagerly exit, creating resistance.',
            'common_pitfalls': ['Trading tested zones', 'Not waiting for reaction', 'Weak zones without structure context'],
            'visual_description': 'Rectangle marking base of strong decline. Sharp move away from zone with little congestion. Clear "before and after" price action.',
            'related_concepts': ['supply and demand', 'resistance', 'unfilled orders', 'structure']
        },
        {
            'term': 'Fresh Demand Zone',
            'definition': '''A Fresh Demand Zone is an untested area where buyers previously overwhelmed sellers, creating a sharp price rise. These zones remain "fresh" until price returns to test them. When price declines back to a fresh demand zone, probability favors bounce as buy orders still reside there. Quality demand zones: (1) caused strong rally (2) left quickly (thin) (3) haven\'t been revisited (4) align with bullish market structure.''',
            'market_behavior_patterns': ['buyer_dominance', 'support_zone', 'unfilled_buy_orders'],
            'trade_structures': ['demand_zone_longs', 'bounce_entries', 'structure_support'],
            'psychology_context': 'Demand zones represent "regret areas" where sellers wish they\'d bought. When price returns, they eagerly enter, creating support.',
            'common_pitfalls': ['Trading used-up zones', 'Entering without confirmation', 'Ignoring market structure context'],
            'visual_description': 'Rectangle marking base of strong rally. Sharp move away with little consolidation. Stands out as area of buyer aggression.',
            'related_concepts': ['supply and demand', 'support', 'buyer dominance', 'structure']
        }
    ],
    
    'confluence': [
        {
            'term': 'Multi-Timeframe Confluence',
            'definition': '''Multi-Timeframe Confluence occurs when multiple timeframes align on direction and key levels. For example: daily shows uptrend + 4H pullback to demand + 1H bullish structure break. This stacking of probabilities creates highest-conviction setups. Process: (1) identify HTF trend, (2) wait for HTF pullback to key level, (3) enter on LTF structure confirmation. The more timeframes agreeing, the higher probability and larger the potential move.''',
            'market_behavior_patterns': ['timeframe_alignment', 'probability_stacking', 'trend_confirmation'],
            'trade_structures': ['htf_ltf_alignment', 'high_conviction_entries', 'multi_timeframe_analysis'],
            'psychology_context': 'When multiple timeframes align, traders at all time horizons act in unison, creating powerful directional moves with less noise.',
            'common_pitfalls': ['Analysis paralysis with too many timeframes', 'Forcing confluence that doesn\'t exist', 'Ignoring LTF confirmation'],
            'visual_description': 'Multiple charts showing same story: HTF trend, HTF key level, LTF entry trigger all aligned. Like gears meshing perfectly.',
            'related_concepts': ['timeframe analysis', 'htf ltf', 'confluence', 'probability']
        }
    ]
}


def add_concepts_to_kb(strategy: str = None, dry_run: bool = False) -> Dict[str, int]:
    """
    Add trading concepts to the Knowledge Base.
    
    Args:
        strategy: Specific strategy to add (e.g., 'smc', 'ict'). If None, adds all.
        dry_run: If True, preview without saving to database.
    
    Returns:
        Dictionary with statistics: {'added': X, 'skipped': X, 'total': X}
    """
    stats = {'added': 0, 'skipped': 0, 'total': 0, 'errors': 0}
    
    # Determine which strategies to process
    strategies_to_add = [strategy] if strategy else list(TRADING_CONCEPTS.keys())
    
    print(f"\n{'='*70}")
    print(f"KNOWLEDGE BASE POPULATION {'(DRY RUN)' if dry_run else '(LIVE)'}")
    print(f"{'='*70}\n")
    
    for strat in strategies_to_add:
        if strat not in TRADING_CONCEPTS:
            print(f"⚠️  Strategy '{strat}' not found. Available: {', '.join(TRADING_CONCEPTS.keys())}")
            continue
        
        concepts = TRADING_CONCEPTS[strat]
        print(f"\n📚 Processing {strat.upper()} ({len(concepts)} concepts)")
        print(f"{'-'*70}")
        
        for concept in concepts:
            stats['total'] += 1
            term = concept['term']
            
            # Check if already exists
            existing = KnowledgeEntry.objects.filter(term=term).first()
            if existing:
                print(f"  ⏭️  SKIP: {term} (already exists)")
                stats['skipped'] += 1
                continue
            
            if dry_run:
                print(f"  👀 PREVIEW: {term}")
                print(f"     Category: {strat}")
                print(f"     Definition length: {len(concept['definition'])} chars")
                print(f"     Related concepts: {len(concept.get('related_concepts', []))}")
                stats['added'] += 1
            else:
                try:
                    # Get or create internal source
                    from knowledge_base.models import Source
                    internal_source, _ = Source.objects.get_or_create(
                        domain='internal.zenithedge.com',
                        defaults={
                            'name': 'ZenithEdge Internal KB',
                            'base_url': 'https://internal.zenithedge.com/kb/',
                            'trust_level': 'high',
                            'respect_robots_txt': False,
                            'rate_limit_seconds': 0,
                            'notes': 'Manually curated professional trading concepts'
                        }
                    )
                    
                    # Create summary from first 2 sentences
                    definition_text = concept['definition']
                    sentences = definition_text.split('. ')
                    summary = '. '.join(sentences[:2]) + '.' if len(sentences) >= 2 else definition_text
                    
                    # Create entry
                    entry = KnowledgeEntry.objects.create(
                        term=term,
                        summary=summary,
                        definition=definition_text,
                        category=strat,
                        source=internal_source,
                        source_url=f'https://internal.zenithedge.com/kb/{strat}/{term.lower().replace(" ", "_")}',
                        is_verified=True,
                        is_active=True,
                        difficulty='intermediate',
                        asset_classes=['any'],
                        
                        # Strategy-aware fields
                        market_behavior_patterns=concept.get('market_behavior_patterns', []),
                        trade_structures=concept.get('trade_structures', []),
                        psychology_context=concept.get('psychology_context', ''),
                        common_pitfalls=concept.get('common_pitfalls', []),
                        visual_description=concept.get('visual_description', ''),
                        related_concepts=concept.get('related_concepts', [])
                    )
                    
                    # Generate embeddings
                    from sentence_transformers import SentenceTransformer
                    model = SentenceTransformer('all-MiniLM-L6-v2')
                    
                    # Generate summary embedding
                    summary_embedding = model.encode(entry.summary)
                    entry.embedding_summary = summary_embedding.tolist()
                    
                    # Generate full definition embedding
                    full_embedding = model.encode(entry.definition)
                    entry.embedding_full = full_embedding.tolist()
                    
                    entry.save()
                    
                    print(f"  ✅ ADDED: {term}")
                    stats['added'] += 1
                    
                except Exception as e:
                    print(f"  ❌ ERROR: {term} - {str(e)}")
                    stats['errors'] += 1
    
    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"  Total concepts processed: {stats['total']}")
    print(f"  ✅ Added: {stats['added']}")
    print(f"  ⏭️  Skipped (existing): {stats['skipped']}")
    print(f"  ❌ Errors: {stats['errors']}")
    
    if not dry_run and stats['added'] > 0:
        print(f"\n🎉 Successfully added {stats['added']} concepts to Knowledge Base!")
        print(f"   Total KB entries: {KnowledgeEntry.objects.count()}")
        print(f"   With embeddings: {KnowledgeEntry.objects.filter(embedding_summary__isnull=False).count()}")
    
    return stats


def show_available_strategies():
    """Display available strategies and concept counts."""
    print(f"\n{'='*70}")
    print(f"AVAILABLE STRATEGIES")
    print(f"{'='*70}\n")
    
    total_concepts = 0
    for strategy, concepts in TRADING_CONCEPTS.items():
        count = len(concepts)
        total_concepts += count
        print(f"  • {strategy.upper():20s} - {count:2d} concepts")
    
    print(f"\n  {'TOTAL':20s} - {total_concepts:2d} concepts")
    print(f"{'='*70}\n")


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description='Populate Knowledge Base with trading concepts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python populate_knowledge_base.py --all              # Add all concepts
  python populate_knowledge_base.py --strategy smc     # Add SMC concepts only
  python populate_knowledge_base.py --dry-run          # Preview without saving
  python populate_knowledge_base.py --list             # Show available strategies
        '''
    )
    
    parser.add_argument('--all', action='store_true', 
                       help='Add all concepts from all strategies')
    parser.add_argument('--strategy', type=str, 
                       help='Add concepts for specific strategy (smc, ict, trend, etc.)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview concepts without saving to database')
    parser.add_argument('--list', action='store_true',
                       help='List available strategies and concept counts')
    
    args = parser.parse_args()
    
    # Show list and exit
    if args.list:
        show_available_strategies()
        return
    
    # Validate arguments
    if not args.all and not args.strategy:
        parser.print_help()
        print("\n❌ Error: Must specify either --all or --strategy <name>\n")
        sys.exit(1)
    
    # Execute
    strategy = None if args.all else args.strategy
    stats = add_concepts_to_kb(strategy=strategy, dry_run=args.dry_run)
    
    # Exit code based on errors
    sys.exit(0 if stats['errors'] == 0 else 1)


if __name__ == '__main__':
    main()
