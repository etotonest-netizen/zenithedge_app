from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import InsightNotification, NotificationPreference
from .manager import NotificationManager
import json


@login_required
@require_http_methods(["GET"])
def notification_list_api(request):
    """API endpoint to get user's notifications"""
    limit = int(request.GET.get('limit', 20))
    unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
    
    notifications = InsightNotification.objects.filter(user=request.user)
    
    if unread_only:
        notifications = notifications.filter(read=False)
    
    notifications = notifications[:limit]
    
    return JsonResponse({
        'notifications': [n.to_dict() for n in notifications],
        'unread_count': NotificationManager.get_unread_count(request.user)
    })


@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read"""
    notification = get_object_or_404(
        InsightNotification,
        id=notification_id,
        user=request.user
    )
    notification.mark_as_read()
    
    return JsonResponse({
        'success': True,
        'notification_id': notification_id,
        'unread_count': NotificationManager.get_unread_count(request.user)
    })


@login_required
@require_http_methods(["POST"])
def mark_all_read(request):
    """Mark all notifications as read for the user"""
    count = NotificationManager.mark_all_as_read(request.user)
    
    return JsonResponse({
        'success': True,
        'count': count,
        'unread_count': 0
    })


@login_required
@require_http_methods(["GET"])
def unread_count_api(request):
    """Get unread notification count"""
    count = NotificationManager.get_unread_count(request.user)
    
    return JsonResponse({
        'unread_count': count
    })


class NotificationPreferencesView(LoginRequiredMixin, TemplateView):
    """View for managing notification preferences"""
    template_name = 'notifications/preferences.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get or create preferences for user
        prefs, created = NotificationPreference.objects.get_or_create(user=self.request.user)
        context['preferences'] = prefs
        
        return context


@login_required
@require_http_methods(["POST"])
def update_preferences(request):
    """Update user's notification preferences"""
    try:
        data = json.loads(request.body)
        
        prefs, created = NotificationPreference.objects.get_or_create(user=request.user)
        
        # Update channel toggles
        if 'web_enabled' in data:
            prefs.web_enabled = data['web_enabled']
        if 'push_enabled' in data:
            prefs.push_enabled = data['push_enabled']
        if 'email_digest_enabled' in data:
            prefs.email_digest_enabled = data['email_digest_enabled']
        
        # Update filters
        if 'min_confidence' in data:
            prefs.min_confidence = max(0, min(100, int(data['min_confidence'])))
        if 'strategies_filter' in data:
            prefs.strategies_filter = data['strategies_filter']
        if 'symbols_filter' in data:
            prefs.symbols_filter = data['symbols_filter']
        
        # Update quiet hours
        if 'quiet_hours_enabled' in data:
            prefs.quiet_hours_enabled = data['quiet_hours_enabled']
        if 'quiet_start_time' in data:
            prefs.quiet_start_time = data['quiet_start_time']
        if 'quiet_end_time' in data:
            prefs.quiet_end_time = data['quiet_end_time']
        
        # Update priority filter
        if 'high_priority_only' in data:
            prefs.high_priority_only = data['high_priority_only']
        
        prefs.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Preferences updated successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
