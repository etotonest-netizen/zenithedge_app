from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os

def quick_entry(request):
    """
    Simple web form for manual signal entry when TradingView Premium is not available.
    Access at: /signals/quick-entry/
    """
    token = os.environ.get('WEBHOOK_TOKEN', 'YOUR_TOKEN_HERE')
    return render(request, 'signals/quick_entry.html', {'token': token})
