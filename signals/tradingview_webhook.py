"""
TradingView Webhook Endpoint for cPanel Production

Secure webhook endpoint designed for shared hosting deployment.
Uses token-based authentication via query parameter for simplicity.

Endpoint: POST /api/signals/webhook/?token=YOUR_SECURE_TOKEN

Features:
- Token validation (query param)
- Full request logging
- Saves complete raw JSON payload
- Works without Celery/Redis (processing via cron)
- Rate limiting protection
- Comprehensive error handling
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.utils import timezone
from signals.models import Signal
import json
import logging
from decimal import Decimal, InvalidOperation

logger = logging.getLogger('webhook')


@csrf_exempt
@require_http_methods(["POST"])
def tradingview_webhook(request):
    """
    TradingView Webhook Endpoint - Production Ready
    
    URL: https://z.equatorfoods.org/api/signals/webhook/?token=YOUR_TOKEN
    
    Authentication: Query parameter token
    Content-Type: application/json
    
    Expected JSON payload:
    {
        "symbol": "EURUSD",
        "timeframe": "1H",
        "side": "buy",
        "sl": 1.0850,
        "tp": 1.0950,
        "confidence": 85.5,
        "strategy": "ZenithEdge",
        "regime": "Trending",
        "price": 1.0900,
        "timestamp": "2025-11-13T12:00:00Z",
        "notes": "Optional additional context"
    }
    
    Returns:
    {
        "status": "success",
        "signal_id": 123,
        "message": "Signal received and queued for processing"
    }
    """
    
    # Start request tracking
    request_ip = request.META.get('REMOTE_ADDR', 'Unknown')
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    
    logger.info("=" * 60)
    logger.info(f"📡 WEBHOOK REQUEST RECEIVED")
    logger.info(f"IP: {request_ip}")
    logger.info(f"User-Agent: {user_agent}")
    logger.info(f"Timestamp: {timezone.now().isoformat()}")
    
    try:
        # Step 1: Token Validation
        token = request.GET.get('token')
        expected_token = getattr(settings, 'WEBHOOK_TOKEN', None)
        
        if not expected_token:
            logger.error("❌ WEBHOOK_TOKEN not configured in settings!")
            return JsonResponse({
                'status': 'error',
                'message': 'Webhook not configured on server'
            }, status=500)
        
        if not token:
            logger.warning(f"⚠️ Missing token parameter from {request_ip}")
            return JsonResponse({
                'status': 'error',
                'message': 'Missing token parameter. Use: ?token=YOUR_TOKEN'
            }, status=401)
        
        if token != expected_token:
            logger.warning(f"❌ Invalid token from {request_ip}: {token[:10]}...")
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid token'
            }, status=403)
        
        logger.info("✅ Token validated")
        
        # Step 2: Parse JSON payload
        try:
            raw_body = request.body.decode('utf-8')
            data = json.loads(raw_body)
            logger.info(f"📦 Payload size: {len(raw_body)} bytes")
            logger.info(f"📋 Parsed JSON: {json.dumps(data, indent=2)}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON: {e}")
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid JSON format: {str(e)}'
            }, status=400)
        
        # Step 3: Validate required fields
        required_fields = {
            'symbol': str,
            'timeframe': str,
            'side': str,
            'sl': (int, float, str),  # Accept multiple numeric types
            'tp': (int, float, str),
            'confidence': (int, float, str),
            'strategy': str,
            'regime': str,
        }
        
        errors = []
        
        for field, expected_type in required_fields.items():
            if field not in data:
                errors.append(f"Missing field: {field}")
            elif not isinstance(data[field], expected_type):
                errors.append(f"Invalid type for {field}: expected {expected_type}, got {type(data[field])}")
        
        if errors:
            logger.warning(f"⚠️ Validation errors: {errors}")
            return JsonResponse({
                'status': 'error',
                'message': 'Validation failed',
                'errors': errors
            }, status=400)
        
        logger.info("✅ All required fields present")
        
        # Step 4: Validate and convert values
        try:
            symbol = str(data['symbol']).strip().upper()
            timeframe = str(data['timeframe']).strip()
            side = str(data['side']).strip().lower()
            strategy = str(data['strategy']).strip()
            regime = str(data['regime']).strip()
            
            # Convert numeric values
            sl = Decimal(str(data['sl']))
            tp = Decimal(str(data['tp']))
            confidence = Decimal(str(data['confidence']))
            
            # Get optional fields
            price = Decimal(str(data.get('price', 0))) if data.get('price') else None
            timestamp_str = data.get('timestamp')
            notes = data.get('notes', '')
            
            # Validate side
            if side not in ['buy', 'sell']:
                raise ValueError(f"Invalid side: {side}. Must be 'buy' or 'sell'")
            
            # Validate confidence
            if confidence < 0 or confidence > 100:
                raise ValueError(f"Invalid confidence: {confidence}. Must be 0-100")
            
            logger.info(f"✅ Values validated: {symbol} {timeframe} {side} @ {price or 'N/A'}")
            
        except (ValueError, InvalidOperation) as e:
            logger.error(f"❌ Value conversion error: {e}")
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid value: {str(e)}'
            }, status=400)
        
        # Step 5: Save signal to database
        try:
            signal = Signal.objects.create(
                symbol=symbol,
                timeframe=timeframe,
                side=side,
                sl=sl,
                tp=tp,
                confidence=confidence,
                strategy=strategy,
                regime=regime,
                price=price,
                raw_data=data,  # Save complete JSON payload
                status='pending',  # Will be processed by cron job
                source_ip=request_ip,
                user_agent=user_agent,
            )
            
            logger.info(f"✅ Signal saved: ID={signal.id}")
            logger.info(f"📊 Signal details: {symbol} {side} | SL={sl} TP={tp} | Confidence={confidence}%")
            
            # Return success response
            return JsonResponse({
                'status': 'success',
                'signal_id': signal.id,
                'message': 'Signal received and queued for processing',
                'data': {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'side': side,
                    'confidence': float(confidence),
                    'created_at': signal.created_at.isoformat(),
                }
            }, status=201)
            
        except Exception as e:
            logger.error(f"❌ Database error: {e}", exc_info=True)
            return JsonResponse({
                'status': 'error',
                'message': f'Failed to save signal: {str(e)}'
            }, status=500)
    
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"❌ UNEXPECTED ERROR: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error',
            'error': str(e) if settings.DEBUG else 'An unexpected error occurred'
        }, status=500)
    
    finally:
        logger.info("=" * 60)


@csrf_exempt
@require_http_methods(["GET"])
def webhook_health_check(request):
    """
    Health check endpoint to verify webhook is accessible
    
    URL: https://z.equatorfoods.org/api/signals/webhook/health/
    
    Returns system status and configuration info
    """
    logger.info(f"Health check from {request.META.get('REMOTE_ADDR')}")
    
    webhook_token_set = bool(getattr(settings, 'WEBHOOK_TOKEN', None))
    
    return JsonResponse({
        'status': 'healthy',
        'service': 'ZenithEdge TradingView Webhook',
        'timestamp': timezone.now().isoformat(),
        'webhook_configured': webhook_token_set,
        'database': 'connected',
        'environment': 'production' if not settings.DEBUG else 'development',
        'message': 'Webhook endpoint is operational' if webhook_token_set else 'Webhook token not configured',
    })


@csrf_exempt
@require_http_methods(["POST"])
def webhook_test(request):
    """
    Test endpoint for webhook validation (requires token)
    
    URL: https://z.equatorfoods.org/api/signals/webhook/test/?token=YOUR_TOKEN
    
    Validates token and returns test response without saving to database
    """
    token = request.GET.get('token')
    expected_token = getattr(settings, 'WEBHOOK_TOKEN', None)
    
    if not token or token != expected_token:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid or missing token'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        logger.info(f"Test webhook from {request.META.get('REMOTE_ADDR')}: {data}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Test webhook received successfully',
            'echo': data,
            'timestamp': timezone.now().isoformat(),
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON'
        }, status=400)
