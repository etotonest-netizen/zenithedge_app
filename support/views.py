from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Max
from django.utils import timezone
from .models import SupportThread, SupportMessage


# ============================================================================
# USER VIEWS
# ============================================================================

@login_required
def support_list(request):
    """
    User view: List all support threads for the logged-in user
    """
    threads = SupportThread.objects.filter(
        user=request.user
    ).annotate(
        message_count=Count('messages')
    ).select_related('user')
    
    # Get unread count for badge
    unread_count = threads.filter(has_unread_admin_message=True).count()
    
    context = {
        'threads': threads,
        'unread_count': unread_count,
    }
    return render(request, 'support/user_list.html', context)


@login_required
def support_thread_detail(request, thread_id):
    """
    User view: View and reply to a specific thread
    """
    thread = get_object_or_404(
        SupportThread,
        id=thread_id,
        user=request.user
    )
    
    # Mark as read by user
    if thread.has_unread_admin_message:
        thread.mark_as_read_by_user()
    
    # Get all messages
    messages = thread.messages.select_related('from_user').all()
    
    # Get related signal and journal if exists
    signal = thread.get_related_signal()
    journal = thread.get_related_journal()
    
    context = {
        'thread': thread,
        'messages': messages,
        'signal': signal,
        'journal': journal,
    }
    return render(request, 'support/thread_detail.html', context)


@login_required
@require_http_methods(["POST"])
def support_create_thread(request):
    """
    User view: Create a new support thread
    """
    subject = request.POST.get('subject', '').strip()
    message_text = request.POST.get('message', '').strip()
    signal_id = request.POST.get('signal_id', '').strip()
    
    if not subject:
        return JsonResponse({'error': 'Subject is required'}, status=400)
    
    # Create thread
    thread = SupportThread.objects.create(
        user=request.user,
        subject=subject,
        signal_id=int(signal_id) if signal_id else None,
        status='open'
    )
    
    # Create initial message if provided
    if message_text:
        SupportMessage.objects.create(
            thread=thread,
            from_user=request.user,
            message=message_text,
            is_admin_message=False
        )
    
    return JsonResponse({
        'success': True,
        'thread_id': thread.id,
        'redirect_url': f'/support/{thread.id}/'
    })


@login_required
@require_http_methods(["POST"])
def support_send_message(request, thread_id):
    """
    User view: Send a message in an existing thread
    """
    thread = get_object_or_404(
        SupportThread,
        id=thread_id,
        user=request.user
    )
    
    message_text = request.POST.get('message', '').strip()
    attachment = request.FILES.get('attachment')
    
    if not message_text:
        return JsonResponse({'error': 'Message cannot be empty'}, status=400)
    
    # Create message
    message = SupportMessage.objects.create(
        thread=thread,
        from_user=request.user,
        message=message_text,
        is_admin_message=False,
        attachment=attachment
    )
    
    return JsonResponse({
        'success': True,
        'message_id': message.id,
        'created_at': message.created_at.strftime('%b %d, %Y %I:%M %p')
    })


# ============================================================================
# ADMIN VIEWS
# ============================================================================

@staff_member_required
def admin_support_inbox(request):
    """
    Admin view: Combined inbox of all support threads
    """
    # Get filter parameter
    status_filter = request.GET.get('status', 'all')
    
    threads = SupportThread.objects.select_related('user').annotate(
        message_count=Count('messages'),
        last_msg_time=Max('messages__created_at')
    )
    
    # Apply filters
    if status_filter == 'open':
        threads = threads.filter(status__in=['open', 'user_replied'])
    elif status_filter == 'awaiting_user':
        threads = threads.filter(status='admin_replied')
    elif status_filter == 'unread':
        threads = threads.filter(has_unread_user_message=True)
    elif status_filter == 'closed':
        threads = threads.filter(status='closed')
    
    # Get statistics
    stats = {
        'total': SupportThread.objects.count(),
        'open': SupportThread.objects.filter(status__in=['open', 'user_replied']).count(),
        'unread': SupportThread.objects.filter(has_unread_user_message=True).count(),
        'closed': SupportThread.objects.filter(status='closed').count(),
    }
    
    context = {
        'threads': threads,
        'status_filter': status_filter,
        'stats': stats,
    }
    return render(request, 'support/admin_inbox.html', context)


@staff_member_required
def admin_support_thread_detail(request, thread_id):
    """
    Admin view: View and respond to a support thread
    """
    thread = get_object_or_404(
        SupportThread.objects.select_related('user'),
        id=thread_id
    )
    
    # Mark as read by admin
    if thread.has_unread_user_message:
        thread.mark_as_read_by_admin()
    
    # Get all messages
    messages = thread.messages.select_related('from_user').all()
    
    # Get related signal and journal if exists
    signal = thread.get_related_signal()
    journal = thread.get_related_journal()
    
    context = {
        'thread': thread,
        'messages': messages,
        'signal': signal,
        'journal': journal,
    }
    return render(request, 'support/admin_thread_detail.html', context)


@staff_member_required
@require_http_methods(["POST"])
def admin_send_message(request, thread_id):
    """
    Admin view: Send a message to user
    """
    thread = get_object_or_404(SupportThread, id=thread_id)
    
    message_text = request.POST.get('message', '').strip()
    attachment = request.FILES.get('attachment')
    
    if not message_text:
        return JsonResponse({'error': 'Message cannot be empty'}, status=400)
    
    # Create admin message
    message = SupportMessage.objects.create(
        thread=thread,
        from_user=request.user,  # Track which admin sent it
        message=message_text,
        is_admin_message=True,
        attachment=attachment
    )
    
    return JsonResponse({
        'success': True,
        'message_id': message.id,
        'created_at': message.created_at.strftime('%b %d, %Y %I:%M %p')
    })


@staff_member_required
@require_http_methods(["POST"])
def admin_close_thread(request, thread_id):
    """
    Admin view: Close a support thread
    """
    thread = get_object_or_404(SupportThread, id=thread_id)
    
    thread.status = 'closed'
    thread.save(update_fields=['status'])
    
    return JsonResponse({
        'success': True,
        'message': 'Thread closed successfully'
    })


@staff_member_required
@require_http_methods(["POST"])
def admin_reopen_thread(request, thread_id):
    """
    Admin view: Reopen a closed thread
    """
    thread = get_object_or_404(SupportThread, id=thread_id)
    
    thread.status = 'open'
    thread.save(update_fields=['status'])
    
    return JsonResponse({
        'success': True,
        'message': 'Thread reopened successfully'
    })


# ============================================================================
# API ENDPOINTS (for notifications/polling)
# ============================================================================

@login_required
def get_unread_count(request):
    """
    API endpoint: Get unread message count for current user
    """
    if request.user.is_staff:
        # Admin: count threads with unread user messages
        count = SupportThread.objects.filter(has_unread_user_message=True).count()
    else:
        # User: count threads with unread admin messages
        count = SupportThread.objects.filter(
            user=request.user,
            has_unread_admin_message=True
        ).count()
    
    return JsonResponse({'unread_count': count})
