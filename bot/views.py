from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
import json

from .models import BotQA, BotConversation, BotSettings, BotChatHistory
from .logic import retrieve_answer
import time
import logging

logger = logging.getLogger('zenbot')


@login_required
@require_http_methods(["POST"])
def chat_api(request):
    """
    Main chat API endpoint for ZenBot.
    Accepts JSON with 'message' field, returns bot response.
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', request.session.session_key)
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': 'Message is required'
            }, status=400)
        
        # Process query through bot engine
        result = retrieve_answer(
            user_query=user_message,
            user=request.user,
            session_id=session_id
        )
        
        return JsonResponse({
            'success': True,
            'response': result['response'],
            'confidence': result['confidence'],
            'category': result['category'],
            'timestamp': timezone.now().isoformat()
        })
        
    except json.JSONDecodeError as e:
        print(f"[ZenBot] JSON decode error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        # Log the full error for debugging
        import traceback
        print(f"[ZenBot] Error in chat_api: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


@login_required
def conversation_history(request):
    """
    Get user's conversation history.
    """
    conversations = BotConversation.objects.filter(
        user=request.user
    ).order_by('-created_at')[:20]
    
    history = [{
        'user_message': conv.user_message,
        'bot_response': conv.bot_response,
        'confidence': conv.confidence_score,
        'timestamp': conv.created_at.isoformat()
    } for conv in conversations]
    
    return JsonResponse({
        'success': True,
        'history': history
    })


@staff_member_required
def admin_panel(request):
    """
    Superuser management interface for bot administration.
    """
    settings = BotSettings.get_settings()
    
    # Statistics
    total_qas = BotQA.objects.filter(is_active=True).count()
    total_conversations = BotConversation.objects.count()
    
    # Recent activity
    recent_convos = BotConversation.objects.order_by('-created_at')[:10]
    
    # Top Q&As by usage
    top_qas = BotQA.objects.filter(is_active=True).order_by('-usage_count')[:10]
    
    # Category breakdown
    category_stats = BotQA.objects.filter(is_active=True).values('category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Low confidence conversations
    low_confidence = BotConversation.objects.filter(
        confidence_score__lt=50.0
    ).order_by('-created_at')[:10]
    
    context = {
        'settings': settings,
        'total_qas': total_qas,
        'total_conversations': total_conversations,
        'recent_convos': recent_convos,
        'top_qas': top_qas,
        'category_stats': category_stats,
        'low_confidence': low_confidence,
    }
    
    return render(request, 'bot/admin_panel.html', context)


@staff_member_required
@require_http_methods(["POST"])
def clear_conversations(request):
    """
    Clear all conversation history.
    """
    try:
        deleted_count = BotConversation.objects.all().delete()[0]
        
        return JsonResponse({
            'success': True,
            'message': f'Deleted {deleted_count} conversations',
            'deleted_count': deleted_count
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@staff_member_required
@require_http_methods(["POST"])
def retrain_bot(request):
    """
    Retrain bot (future feature - currently resets usage counters).
    """
    try:
        # Reset usage counters
        BotQA.objects.all().update(usage_count=0)
        
        return JsonResponse({
            'success': True,
            'message': 'Bot retrained successfully (usage counters reset)'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@staff_member_required
@require_http_methods(["POST"])
def update_settings(request):
    """
    Update bot settings via AJAX.
    """
    try:
        data = json.loads(request.body)
        settings = BotSettings.get_settings()
        
        if 'match_threshold' in data:
            settings.match_threshold = float(data['match_threshold'])
        if 'enable_user_stats' in data:
            settings.enable_user_stats = bool(data['enable_user_stats'])
        if 'enable_signal_queries' in data:
            settings.enable_signal_queries = bool(data['enable_signal_queries'])
        if 'enable_learning' in data:
            settings.enable_learning = bool(data['enable_learning'])
        if 'default_fallback_message' in data:
            settings.default_fallback_message = data['default_fallback_message']
        
        settings.updated_by = request.user
        settings.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Settings updated successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# =============================================================================
# Bot /ask Endpoint with Slash Commands
# =============================================================================

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def bot_ask(request):
    """
    Enhanced ZenBot endpoint with slash command support.
    
    Supported commands:
    - /score <signal_id> - Get AI score breakdown
    - /prop status - Get prop challenge status
    - /strategy stats - Get strategy performance
    
    POST body: {"prompt": "...", "session_id": "..."}
    """
    start_time = time.time()
    
    try:
        data = json.loads(request.body)
        prompt = data.get('prompt', '').strip()
        session_id = data.get('session_id', '')
        
        if not prompt:
            return JsonResponse({'status': 'error', 'message': 'Prompt required'}, status=400)
        
        # Check if it's a command
        is_command = prompt.startswith('/')
        command_type = ''
        response = ''
        
        if is_command:
            command_type, response = execute_command(prompt, request.user)
        else:
            response = get_qa_response(prompt, request.user)
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Save to chat history
        BotChatHistory.objects.create(
            user=request.user,
            prompt=prompt,
            response=response,
            is_command=is_command,
            command_type=command_type,
            session_id=session_id,
            response_time_ms=response_time_ms
        )
        
        logger.info(f"ZenBot: {request.user.email} | {command_type or 'chat'} | {response_time_ms}ms")
        
        return JsonResponse({
            'status': 'success',
            'response': response,
            'is_command': is_command,
            'command_type': command_type,
            'response_time_ms': response_time_ms
        })
        
    except Exception as e:
        logger.error(f"ZenBot error: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def execute_command(command_str, user):
    """Execute slash commands"""
    parts = command_str.strip().split()
    command = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    
    if command == '/score':
        if not args:
            return ('score', 'Usage: /score <signal_id>')
        try:
            return get_signal_score(int(args[0]), user)
        except ValueError:
            return ('score', f'Invalid signal ID: {args[0]}')
    
    elif command in ['/prop', '/propstatus']:
        return get_prop_status(user)
    
    elif command in ['/strategy', '/strat']:
        return get_strategy_stats(user, ' '.join(args) if args else None)
    
    elif command == '/help':
        return ('help', get_help_text())
    
    else:
        return ('unknown', f'Unknown command: {command}. Type /help for commands.')


def get_signal_score(signal_id, user):
    """Get AI score breakdown"""
    from signals.models import Signal
    
    try:
        signal = Signal.objects.select_related('ai_score').get(id=signal_id, user=user)
        
        if not hasattr(signal, 'ai_score') or not signal.ai_score:
            return ('score', f'Signal #{signal_id} has not been scored yet.')
        
        score = signal.ai_score
        lines = [
            f"📊 Signal #{signal_id} AI Score: {score.ai_score}/100",
            f"Symbol: {signal.symbol} | Side: {signal.side.upper()}",
            f"Strategy: {signal.strategy} | Regime: {signal.regime}",
            f"\nScore Breakdown:"
        ]
        
        if score.score_breakdown:
            for item in score.score_breakdown:
                lines.append(f"• {item.get('factor')}: {item.get('raw_value')} → +{item.get('contribution', 0)*100:.0f} pts")
        
        return ('score', '\n'.join(lines))
        
    except Signal.DoesNotExist:
        return ('score', f'Signal #{signal_id} not found.')


def get_prop_status(user):
    """Get prop challenge status"""
    from signals.models import PropChallengeConfig
    
    try:
        challenge = PropChallengeConfig.objects.get(user=user, is_active=True)
        progress = challenge.progress
        
        lines = [
            f"💰 Prop Challenge: {challenge.get_firm_name_display()}",
            f"Account: ${challenge.account_size:,.0f}",
            f"Current Balance: ${progress.get_current_balance():,.2f}",
            f"P&L: ${progress.total_pnl:+,.2f}",
            f"Win Rate: {(progress.winning_trades/progress.total_trades*100) if progress.total_trades else 0:.1f}%",
            f"Daily Loss Remaining: ${progress.get_daily_loss_remaining():,.2f}",
            f"Trading Days: {progress.trading_days}/{challenge.min_trading_days}"
        ]
        
        return ('prop', '\n'.join(lines))
        
    except PropChallengeConfig.DoesNotExist:
        return ('prop', 'No active prop challenge found.')


def get_strategy_stats(user, strategy_name=None):
    """Get strategy stats"""
    from signals.models import StrategyPerformance
    
    if strategy_name:
        perfs = StrategyPerformance.objects.filter(user=user, strategy_name__icontains=strategy_name)
    else:
        perfs = StrategyPerformance.objects.filter(user=user, total_trades__gte=5).order_by('-win_rate')[:5]
    
    if not perfs.exists():
        return ('strategy', 'No strategy statistics available yet.')
    
    lines = ["📊 Strategy Performance:"]
    for perf in perfs:
        lines.append(f"\n{perf.strategy_name}:")
        lines.append(f"  Win Rate: {perf.win_rate:.1f}% | Trades: {perf.total_trades}")
        lines.append(f"  R:R: {perf.avg_rr:.2f} | P/L: {perf.total_pnl:+,.2f}")
    
    return ('strategy', '\n'.join(lines))


def get_qa_response(prompt, user):
    """Get response from Q&A"""
    settings = BotSettings.get_settings()
    prompt_lower = prompt.lower()
    
    qa_entries = BotQA.objects.filter(is_active=True).order_by('-priority', '-usage_count')
    
    best_match = None
    best_score = 0
    
    for qa in qa_entries:
        questions = [q.strip().lower() for q in qa.question.split('|')]
        
        for question in questions:
            prompt_words = set(prompt_lower.split())
            question_words = set(question.split())
            common = prompt_words & question_words
            
            if question_words:
                similarity = len(common) / len(question_words) * 100
                if similarity > best_score and similarity >= settings.match_threshold:
                    best_score = similarity
                    best_match = qa
    
    if best_match:
        best_match.increment_usage()
        return best_match.answer
    
    return settings.default_fallback_message


def get_help_text():
    """Return help text"""
    return """ZenBot Commands:
/score <id> - Get AI score for signal
/prop status - Prop challenge status
/strategy stats - Strategy performance
/help - Show this help"""
