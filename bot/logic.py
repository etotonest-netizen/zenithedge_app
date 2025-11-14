"""
ZenBot Logic Module
Handles Q&A matching, user stats queries, and intelligent responses.
"""
from difflib import SequenceMatcher
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
import re

from .models import BotQA, BotConversation, BotSettings


class ZenBotEngine:
    """
    Core bot intelligence engine for ZenithEdge.
    """
    
    def __init__(self, user=None):
        self.user = user
        self.settings = BotSettings.get_settings()
    
    def process_query(self, user_message, session_id=None):
        """
        Main entry point for processing user queries.
        Returns bot response with metadata.
        """
        user_message = user_message.strip()
        
        # Check for dynamic queries first (user stats, signals, etc.)
        dynamic_response = self._check_dynamic_queries(user_message)
        if dynamic_response:
            confidence = 95.0
            matched_qa = None
            response = dynamic_response
        else:
            # Try Q&A matching
            matched_qa, confidence = self._find_best_match(user_message)
            
            if matched_qa and confidence >= self.settings.match_threshold:
                response = matched_qa.answer
                matched_qa.increment_usage()
            else:
                response = self.settings.default_fallback_message
                confidence = 0.0
        
        # Save conversation history
        if self.user and session_id:
            BotConversation.objects.create(
                user=self.user,
                session_id=session_id,
                user_message=user_message,
                bot_response=response,
                matched_qa=matched_qa,
                confidence_score=confidence
            )
        
        return {
            'response': response,
            'confidence': confidence,
            'matched_qa_id': matched_qa.id if matched_qa else None,
            'category': matched_qa.category if matched_qa else None
        }
    
    def _find_best_match(self, query):
        """
        Find best matching Q&A using similarity scoring.
        Enhanced with Knowledge Base v2.0 integration.
        Returns (BotQA object, confidence_score) or (None, 0.0)
        """
        query_lower = query.lower()
        
        # First, try Knowledge Base v2.0 for trading concepts
        kb_result = self._try_knowledge_base(query)
        if kb_result and kb_result['confidence'] >= 60:
            # Create a virtual BotQA response from KB
            return self._create_virtual_qa(kb_result), kb_result['confidence']
        
        # Fall back to traditional Q&A matching
        active_qas = BotQA.objects.filter(is_active=True)
        
        best_match = None
        best_score = 0.0
        
        for qa in active_qas:
            # Check all question variations (separated by |)
            questions = [q.strip() for q in qa.question.split('|')]
            
            for question in questions:
                question_lower = question.lower()
                
                # Calculate similarity score
                score = self._calculate_similarity(query_lower, question_lower)
                
                # Boost score if keywords match
                if qa.keywords:
                    keywords = [k.strip().lower() for k in qa.keywords.split(',')]
                    keyword_matches = sum(1 for kw in keywords if kw in query_lower)
                    if keyword_matches > 0:
                        score += (keyword_matches * 10)
                
                # Apply priority boost
                score += (qa.priority * 0.5)
                
                if score > best_score:
                    best_score = score
                    best_match = qa
        
        # If KB result is better than traditional Q&A, use KB
        if kb_result and kb_result['confidence'] > best_score:
            return self._create_virtual_qa(kb_result), kb_result['confidence']
        
        return best_match, min(best_score, 100.0)
    
    def _try_knowledge_base(self, query):
        """
        Try to answer question using Knowledge Base v2.0.
        Returns KB result dict or None.
        """
        try:
            from bot.kb_integration import answer_trading_question
            
            # Check if question is trading-related
            trading_keywords = [
                'order block', 'fair value gap', 'liquidity', 'sweep', 
                'trend', 'breakout', 'support', 'resistance', 'supply', 'demand',
                'smc', 'ict', 'smart money', 'institutional', 'structure',
                'entry', 'stop loss', 'take profit', 'setup', 'pattern',
                'market', 'price', 'chart', 'trade', 'strategy'
            ]
            
            query_lower = query.lower()
            is_trading_question = any(keyword in query_lower for keyword in trading_keywords)
            
            if not is_trading_question:
                return None
            
            # Query Knowledge Base
            result = answer_trading_question(query, context={'user': self.user})
            
            # Return if confidence is sufficient
            if result['confidence'] >= 40:
                return result
            
            return None
            
        except Exception as e:
            # Log error but don't fail the whole query
            import logging
            logger = logging.getLogger('zenbot')
            logger.warning(f"KB integration error: {e}")
            return None
    
    def _create_virtual_qa(self, kb_result):
        """
        Create a virtual BotQA object from KB result for compatibility.
        """
        class VirtualQA:
            def __init__(self, answer, category):
                self.answer = answer
                self.category = category
                self.id = None
            
            def increment_usage(self):
                pass  # Virtual QA doesn't track usage
        
        return VirtualQA(
            answer=kb_result['answer'],
            category=kb_result.get('strategy', 'knowledge_base')
        )
    
    def _calculate_similarity(self, str1, str2):
        """
        Calculate similarity between two strings (0-100).
        Uses SequenceMatcher for fuzzy matching.
        """
        # Exact match
        if str1 == str2:
            return 100.0
        
        # Substring match
        if str1 in str2 or str2 in str1:
            return 85.0
        
        # Word-based matching
        words1 = set(str1.split())
        words2 = set(str2.split())
        common_words = words1.intersection(words2)
        
        if common_words:
            word_score = (len(common_words) / max(len(words1), len(words2))) * 70
        else:
            word_score = 0
        
        # Character-based similarity
        char_score = SequenceMatcher(None, str1, str2).ratio() * 60
        
        return max(word_score, char_score)
    
    def _check_dynamic_queries(self, query):
        """
        Check for dynamic queries that require database lookups.
        Returns response string or None.
        """
        if not self.user:
            return None
        
        query_lower = query.lower()
        

        # AI Score commands (check first - specific syntax)
        score_response = self._check_score_commands(query)
        if score_response:
            return score_response
        # Challenge status queries
        if any(word in query_lower for word in ['challenge', 'prop', 'ftmo', 'progress', 'pass', 'fail']):
            return self._get_challenge_status()
        
        # Signal statistics queries
        if any(word in query_lower for word in ['signals', 'trades', 'win rate', 'performance', 'statistics']):
            return self._get_signal_stats()
        
        # Risk control queries
        if any(word in query_lower for word in ['risk', 'halted', 'control', 'threshold', 'limits']):
            return self._get_risk_status()
        
        # Recent trades queries
        if any(word in query_lower for word in ['recent', 'latest', 'last trade', 'today']):
            return self._get_recent_trades()
        
        # Account summary queries
        if any(word in query_lower for word in ['summary', 'overview', 'account', 'my stats']):
            return self._get_account_summary()
        
        return None
    
    def _get_challenge_status(self):
        """Query user's prop challenge status"""
        if not self.settings.enable_user_stats:
            return None
        
        try:
            from signals.models import PropChallengeConfig, PropChallengeProgress
            
            challenge = PropChallengeConfig.objects.filter(
                user=self.user,
                is_active=True
            ).first()
            
            if not challenge:
                return "You don't have an active prop challenge. Visit the Challenge Setup page to create one!"
            
            progress = PropChallengeProgress.objects.filter(challenge=challenge).first()
            
            if not progress:
                return f"Your {challenge.get_firm_name_display()} challenge is configured but not started yet."
            
            status_emoji = progress.get_status_indicator()
            balance = progress.get_current_balance()
            profit_progress = progress.get_profit_progress_pct()
            daily_loss_remaining = progress.get_daily_loss_remaining()
            
            response = f"{status_emoji} **{challenge.get_firm_name_display()} Challenge Status:**\n\n"
            response += f"• Status: {progress.status.upper()}\n"
            response += f"• Current Balance: ${balance:,.2f}\n"
            response += f"• Total P&L: ${progress.total_pnl:,.2f}\n"
            response += f"• Profit Target Progress: {profit_progress:.1f}%\n"
            response += f"• Daily Loss Remaining: ${daily_loss_remaining:,.2f}\n"
            response += f"• Trading Days: {progress.trading_days}/{challenge.min_trading_days}\n"
            response += f"• Win Rate: {(progress.winning_trades / max(progress.total_trades, 1) * 100):.1f}%\n"
            
            if progress.daily_loss_violations > 0 or progress.overall_loss_violations > 0:
                response += f"\n⚠️ Violations: {progress.daily_loss_violations + progress.overall_loss_violations} total"
            
            return response
            
        except ImportError:
            return None
    
    def _get_signal_stats(self):
        """Query user's signal statistics"""
        if not self.settings.enable_signal_queries:
            return None
        
        try:
            from signals.models import Signal
            
            signals = Signal.objects.filter(user=self.user)
            total_signals = signals.count()
            
            if total_signals == 0:
                return "You don't have any trading signals yet. Connect your TradingView webhook to start receiving signals!"
            
            # Count by outcome
            green_signals = signals.filter(outcome='green').count()
            red_signals = signals.filter(outcome='red').count()
            pending_signals = signals.filter(outcome='pending').count()
            
            # Calculate win rate
            completed_signals = green_signals + red_signals
            win_rate = (green_signals / max(completed_signals, 1)) * 100 if completed_signals > 0 else 0
            
            # Strategy breakdown
            strategy_stats = signals.values('strategy').annotate(count=Count('id')).order_by('-count')
            
            # Regime breakdown
            regime_stats = signals.values('regime').annotate(count=Count('id')).order_by('-count')
            
            response = f"📊 **Your Trading Statistics:**\n\n"
            response += f"• Total Signals: {total_signals}\n"
            response += f"• Green (Wins): {green_signals}\n"
            response += f"• Red (Losses): {red_signals}\n"
            response += f"• Pending: {pending_signals}\n"
            response += f"• Win Rate: {win_rate:.1f}%\n"
            
            if strategy_stats:
                response += f"\n**Strategy Breakdown:**\n"
                for stat in strategy_stats[:3]:
                    response += f"• {stat['strategy'] or 'Unknown'}: {stat['count']} signals\n"
            
            if regime_stats:
                response += f"\n**Market Regime:**\n"
                for stat in regime_stats[:2]:
                    response += f"• {stat['regime'] or 'Unknown'}: {stat['count']} signals\n"
            
            return response
            
        except ImportError:
            return None
    
    def _get_risk_status(self):
        """Query user's risk control status"""
        try:
            from signals.models import RiskControl, Signal
            
            risk = RiskControl.objects.filter(user=self.user).first()
            
            if not risk:
                return "Risk control is not configured for your account. Visit the dashboard to set it up!"
            
            # Calculate consecutive losses
            recent_signals = Signal.objects.filter(
                user=self.user
            ).order_by('-received_at')[:10]
            
            consecutive_losses = 0
            for signal in recent_signals:
                if signal.outcome == 'red':
                    consecutive_losses += 1
                elif signal.outcome == 'green':
                    break
            
            status_icon = "🛑" if risk.is_halted else "✅"
            
            response = f"{status_icon} **Risk Control Status:**\n\n"
            response += f"• Status: {'HALTED' if risk.is_halted else 'ACTIVE'}\n"
            response += f"• Max Consecutive Losers: {risk.max_consecutive_losers}\n"
            response += f"• Current Consecutive Losses: {consecutive_losses}\n"
            response += f"• Max Daily Trades: {risk.max_daily_trades}\n"
            response += f"• Max Red Signals Per Day: {risk.max_red_signals_per_day}\n"
            
            if risk.is_halted:
                response += f"\n⚠️ Trading is currently halted. Reason: {risk.halt_reason or 'Manual halt'}"
                if risk.halt_triggered_at:
                    response += f"\n   Halted at: {risk.halt_triggered_at.strftime('%Y-%m-%d %H:%M')}"
            
            return response
            
        except ImportError:
            return None
    
    def _get_recent_trades(self):
        """Query user's recent trades"""
        try:
            from signals.models import Signal
            
            recent = Signal.objects.filter(
                user=self.user
            ).order_by('-received_at')[:5]
            
            if not recent:
                return "You don't have any recent trades."
            
            response = "📈 **Your Recent Trades:**\n\n"
            
            for signal in recent:
                outcome_icon = {
                    'green': '✅',
                    'red': '❌',
                    'pending': '⏳'
                }.get(signal.outcome, '❔')
                
                response += f"{outcome_icon} {signal.symbol} {signal.side} - {signal.strategy or 'Unknown'}\n"
                response += f"   Entry: ${signal.price:.2f} | SL: ${signal.sl:.2f} | TP: ${signal.tp:.2f}\n"
                response += f"   Confidence: {signal.confidence}% | {signal.received_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            
            return response
            
        except ImportError:
            return None
    
    def _get_account_summary(self):
        """Get comprehensive account overview"""
        try:
            from signals.models import Signal, PropChallengeConfig, RiskControl
            
            # Signal stats
            total_signals = Signal.objects.filter(user=self.user).count()
            green_signals = Signal.objects.filter(user=self.user, outcome='green').count()
            red_signals = Signal.objects.filter(user=self.user, outcome='red').count()
            win_rate = (green_signals / max(green_signals + red_signals, 1)) * 100 if (green_signals + red_signals) > 0 else 0
            
            # Challenge status
            challenge = PropChallengeConfig.objects.filter(user=self.user, is_active=True).first()
            challenge_text = f"{challenge.get_firm_name_display()} Challenge" if challenge else "No active challenge"
            
            # Risk status
            risk = RiskControl.objects.filter(user=self.user).first()
            risk_text = "HALTED" if (risk and risk.is_halted) else "ACTIVE" if risk else "Not Configured"
            
            response = f"📊 **Account Summary:**\n\n"
            response += f"• Total Signals: {total_signals}\n"
            response += f"• Win Rate: {win_rate:.1f}%\n"
            response += f"• Challenge: {challenge_text}\n"
            response += f"• Risk Control: {risk_text}\n"
            response += f"\nFor detailed stats, ask me about 'signals', 'challenge', or 'risk'!"
            
            return response
            
        except ImportError:
            return None


    def _check_score_commands(self, query):
        """
        Check for AI scoring commands: /score, /score-why, /score-weights, /score-optimize
        """
        query_lower = query.lower().strip()
        
        # /score <signal_id> - Friendly explanation
        if query_lower.startswith('/score ') or query_lower.startswith('score '):
            parts = query.split()
            if len(parts) >= 2:
                try:
                    signal_id = int(parts[1])
                    return self._get_score_explanation(signal_id)
                except ValueError:
                    return "❌ Invalid signal ID. Usage: /score <signal_id>"
        
        # /score-why <signal_id> - Technical breakdown
        if query_lower.startswith('/score-why ') or query_lower.startswith('score-why '):
            parts = query.split()
            if len(parts) >= 2:
                try:
                    signal_id = int(parts[1])
                    return self._get_score_breakdown(signal_id)
                except ValueError:
                    return "❌ Invalid signal ID. Usage: /score-why <signal_id>"
        
        # /score-weights - Show current weights
        if '/score-weights' in query_lower or 'score weights' in query_lower:
            return self._get_scoring_weights()
        
        # /score-optimize - Admin only
        if '/score-optimize' in query_lower or 'score optimize' in query_lower:
            if self.user and self.user.is_superuser:
                return self._optimize_scoring_weights()
            else:
                return "🔒 This command is only available to administrators."
        
        return None
    
    def _get_score_explanation(self, signal_id):
        """Get friendly AI score explanation for a signal"""
        try:
            from signals.models import Signal, TradeScore
            
            signal = Signal.objects.filter(id=signal_id, user=self.user).first()
            if not signal:
                return f"❌ Signal #{signal_id} not found or doesn't belong to you."
            
            try:
                trade_score = signal.ai_score
                badge = trade_score.get_score_badge()
                key_factors = trade_score.get_key_factors()
                
                response = f"{badge['icon']} **Signal #{signal_id} AI Score: {trade_score.ai_score}/100** ({badge['label']})\n\n"
                response += f"**{signal.symbol}** {signal.side.upper()} @ ${signal.price}\n"
                response += f"Strategy: {signal.strategy} | Regime: {signal.regime}\n\n"
                
                response += "**Score Breakdown:**\n"
                for item in trade_score.score_breakdown:
                    factor = item.get('factor', 'Unknown')
                    raw = item.get('raw_value', 'N/A')
                    contrib = item.get('contribution', 0)
                    response += f"• {factor}: {raw} → +{int(contrib*100)} pts\n"
                
                if key_factors:
                    response += f"\n✨ **Standout Factors:** {', '.join(key_factors)}"
                
                response += f"\n\n_Scored with engine v{trade_score.version}_"
                return response
                
            except TradeScore.DoesNotExist:
                return f"⚠️ Signal #{signal_id} hasn't been scored yet. Scores are generated automatically for new signals."
        
        except Exception as e:
            return f"❌ Error retrieving score: {str(e)}"
    
    def _get_score_breakdown(self, signal_id):
        """Get technical JSON breakdown of score factors"""
        try:
            from signals.models import Signal, TradeScore
            import json
            
            signal = Signal.objects.filter(id=signal_id, user=self.user).first()
            if not signal:
                return f"❌ Signal #{signal_id} not found."
            
            try:
                trade_score = signal.ai_score
                breakdown = {
                    'signal_id': signal_id,
                    'ai_score': trade_score.ai_score,
                    'version': trade_score.version,
                    'factors': {
                        'confidence': trade_score.confidence_factor,
                        'atr_safety': trade_score.atr_safety_factor,
                        'strategy_bias': trade_score.strategy_bias_factor,
                        'regime_fit': trade_score.regime_fit_factor,
                        'rolling_win_rate': trade_score.rolling_win_rate
                    },
                    'breakdown': trade_score.score_breakdown
                }
                
                return f"```json\n{json.dumps(breakdown, indent=2)}\n```"
                
            except TradeScore.DoesNotExist:
                return f"❌ No score found for signal #{signal_id}"
        
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def _get_scoring_weights(self):
        """Show current scoring weights configuration"""
        try:
            from signals.models import ScoringWeights
            
            weights_obj = ScoringWeights.get_active_weights()
            
            response = f"⚙️ **Active Scoring Weights (v{weights_obj.version})**\n\n"
            
            for key, value in weights_obj.weights.items():
                response += f"• {key.replace('_', ' ').title()}: {value:.2%}\n"
            
            response += f"\n🎯 Minimum Score Threshold: {weights_obj.min_score_threshold}\n"
            
            if weights_obj.notes:
                response += f"\n📝 Notes: {weights_obj.notes}\n"
            
            response += f"\n_Last updated: {weights_obj.updated_at.strftime('%Y-%m-%d %H:%M')}_"
            
            return response
            
        except Exception as e:
            return f"❌ Error retrieving weights: {str(e)}"
    
    def _optimize_scoring_weights(self):
        """Run weight optimization based on recent performance (admin only)"""
        try:
            from bot.score_engine import update_weights_from_journal
            from signals.models import ScoringWeights
            
            result = update_weights_from_journal(window_days=30, learning_rate=0.1)
            
            if result['status'] == 'success':
                # Create new version
                import datetime
                new_version = f"v{datetime.datetime.now().strftime('%Y%m%d-%H%M')}"
                
                ScoringWeights.objects.create(
                    version=new_version,
                    weights=result['new_weights'],
                    is_active=True,
                    notes=f"Auto-optimized from {result['analyzed_signals']} signals with {result['win_rate']:.1%} win rate"
                )
                
                response = f"✅ **Scoring weights optimized!**\n\n"
                response += f"Analyzed: {result['analyzed_signals']} signals\n"
                response += f"Win Rate: {result['win_rate']:.1%}\n\n"
                
                response += "**Weight Changes:**\n"
                for key in result['new_weights']:
                    old = result['old_weights'].get(key, 0)
                    new = result['new_weights'][key]
                    change = new - old
                    arrow = "��" if change > 0 else "📉" if change < 0 else "➡️"
                    response += f"{arrow} {key}: {old:.2%} → {new:.2%}\n"
                
                response += f"\n_New version: {new_version}_"
                return response
                
            elif result['status'] == 'insufficient_data':
                return f"⚠️ {result['message']}"
            else:
                return f"❌ Optimization failed: {result.get('message', 'Unknown error')}"
                
        except Exception as e:
            return f"❌ Error during optimization: {str(e)}"

def retrieve_answer(user_query, user=None, session_id=None):
    """
    Public API for retrieving bot answers.
    Usage: retrieve_answer("What is trend following?", user=request.user)
    """
    engine = ZenBotEngine(user=user)
    return engine.process_query(user_query, session_id=session_id)


def query_signal_stats(user):
    """Direct query for signal statistics"""
    engine = ZenBotEngine(user=user)
    return engine._get_signal_stats()


def query_challenge_status(user):
    """Direct query for prop challenge status"""
    engine = ZenBotEngine(user=user)
    return engine._get_challenge_status()


def query_risk_control(user):
    """Direct query for risk control status"""
    engine = ZenBotEngine(user=user)
    return engine._get_risk_status()

