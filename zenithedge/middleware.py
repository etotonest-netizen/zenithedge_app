"""
Custom middleware for ZenithEdge Trading Hub
"""
import time
import hashlib
from collections import defaultdict
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to responses.
    Implements CSP, HSTS, and other security best practices.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Content Security Policy (Updated to allow Google Fonts)
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com https://fonts.googleapis.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' data: https://cdn.jsdelivr.net https://fonts.gstatic.com; "
            "connect-src 'self' https://cdn.jsdelivr.net; "
            "frame-ancestors 'none';"
        )
        
        # Additional security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # HSTS (only in production with HTTPS)
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        return response


class WebhookRateLimitMiddleware:
    """
    Middleware to implement rate limiting for webhook endpoints.
    Uses in-memory sliding window counter per UUID/IP.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # In-memory rate limit storage: {identifier: [(timestamp, count), ...]}
        self.rate_limits = defaultdict(list)
        self.cleanup_interval = 60  # Clean up old entries every 60 seconds
        self.last_cleanup = time.time()

    def __call__(self, request):
        # Only apply to webhook endpoints
        if request.path.startswith('/api/v1/signal/'):
            # Extract UUID from path
            path_parts = request.path.strip('/').split('/')
            if len(path_parts) >= 4:
                webhook_uuid = path_parts[3]
                
                # Get client identifier (UUID + IP for extra security)
                client_ip = self.get_client_ip(request)
                identifier = f"{webhook_uuid}:{client_ip}"
                
                # Check rate limit
                if not self.check_rate_limit(identifier):
                    return JsonResponse({
                        'error': 'Rate limit exceeded',
                        'message': f'Maximum {settings.WEBHOOK_RATE_LIMIT} requests per second allowed',
                        'retry_after': 1
                    }, status=429)
        
        # Periodic cleanup of old entries
        self.cleanup_old_entries()
        
        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def check_rate_limit(self, identifier):
        """
        Check if request is within rate limit.
        Uses sliding window algorithm.
        """
        now = time.time()
        window_start = now - 1.0  # 1 second window
        
        # Get existing requests in current window
        requests = self.rate_limits[identifier]
        
        # Filter to only requests in current window
        recent_requests = [ts for ts in requests if ts > window_start]
        
        # Check if under limit
        rate_limit = getattr(settings, 'WEBHOOK_RATE_LIMIT', 10)
        if len(recent_requests) >= rate_limit:
            return False
        
        # Add current request
        recent_requests.append(now)
        self.rate_limits[identifier] = recent_requests
        
        return True

    def cleanup_old_entries(self):
        """Remove old rate limit entries to prevent memory bloat"""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        self.last_cleanup = now
        cutoff = now - 60  # Keep last 60 seconds
        
        # Clean up old entries
        for identifier in list(self.rate_limits.keys()):
            self.rate_limits[identifier] = [
                ts for ts in self.rate_limits[identifier] 
                if ts > cutoff
            ]
            # Remove empty lists
            if not self.rate_limits[identifier]:
                del self.rate_limits[identifier]


class HMACSignatureMiddleware:
    """
    Middleware to validate HMAC signatures on webhook requests.
    Optional - only validates if webhook config has secret key set.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only apply to webhook endpoints
        if request.path.startswith('/api/v1/signal/') and request.method == 'POST':
            # Check if signature validation is enabled
            signature = request.headers.get('X-ZenithEdge-Signature')
            if signature:
                # Validate signature
                if not self.validate_signature(request, signature):
                    return JsonResponse({
                        'error': 'Invalid signature',
                        'message': 'HMAC signature validation failed'
                    }, status=401)
        
        response = self.get_response(request)
        return response

    def validate_signature(self, request, provided_signature):
        """
        Validate HMAC signature.
        Signature format: sha256=<hex_digest>
        """
        import hmac
        import hashlib
        
        # Extract UUID from path
        path_parts = request.path.strip('/').split('/')
        if len(path_parts) < 4:
            return False
        
        webhook_uuid = path_parts[3]
        
        # Get webhook config and secret
        try:
            from signals.models import WebhookConfig
            webhook_config = WebhookConfig.objects.get(webhook_uuid=webhook_uuid)
            
            # Check if secret is configured
            secret = getattr(webhook_config, 'hmac_secret', None)
            if not secret:
                # No secret configured, skip validation
                return True
            
            # Compute HMAC
            body = request.body
            computed_signature = hmac.new(
                secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures (constant-time comparison)
            expected = f"sha256={computed_signature}"
            return hmac.compare_digest(expected, provided_signature)
            
        except Exception:
            # If any error occurs, fail closed (reject request)
            return False
