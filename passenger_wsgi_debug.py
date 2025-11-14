"""
Debug WSGI - Shows detailed error information
Replace passenger_wsgi.py with this temporarily to see what's failing
"""
import sys
import os
import traceback

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

def application(environ, start_response):
    """Debug application that shows all errors"""
    
    output_lines = [
        "<!DOCTYPE html><html><head><title>Debug Info</title>",
        "<style>body{font-family:monospace;margin:20px;} .ok{color:green;} .error{color:red;background:#fee;padding:10px;}</style>",
        "</head><body><h1>Debug Information</h1>"
    ]
    
    try:
        # Check 1: Python environment
        output_lines.append(f"<p class='ok'>✅ Python: {sys.version}</p>")
        output_lines.append(f"<p class='ok'>✅ Current Dir: {CURRENT_DIR}</p>")
        output_lines.append(f"<p class='ok'>✅ Sys Path: {sys.path[:3]}</p>")
        
        # Check 2: Environment variables
        output_lines.append("<h2>Environment Variables:</h2><ul>")
        for key in ['DJANGO_SETTINGS_MODULE', 'DB_NAME', 'DB_USER', 'WEBHOOK_TOKEN']:
            val = os.environ.get(key, 'NOT SET')
            if val != 'NOT SET':
                output_lines.append(f"<li class='ok'>✅ {key}: {val[:20]}...</li>")
            else:
                output_lines.append(f"<li class='error'>❌ {key}: NOT SET</li>")
        output_lines.append("</ul>")
        
        # Check 3: Django import
        try:
            import django
            output_lines.append(f"<p class='ok'>✅ Django imported: {django.VERSION}</p>")
        except Exception as e:
            output_lines.append(f"<p class='error'>❌ Django import failed: {e}</p>")
            raise
        
        # Check 4: Settings import
        try:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings_production')
            from django.conf import settings
            output_lines.append(f"<p class='ok'>✅ Settings loaded: {settings.DEBUG}</p>")
            output_lines.append(f"<p class='ok'>✅ Database: {settings.DATABASES['default']['ENGINE']}</p>")
        except Exception as e:
            output_lines.append(f"<p class='error'>❌ Settings failed: {e}</p>")
            output_lines.append(f"<pre>{traceback.format_exc()}</pre>")
            raise
        
        # Check 5: WSGI application
        try:
            from django.core.wsgi import get_wsgi_application
            django_app = get_wsgi_application()
            output_lines.append(f"<p class='ok'>✅ WSGI application created</p>")
            
            # Try to actually run it
            output_lines.append("<h2>Attempting to run Django WSGI...</h2>")
            return django_app(environ, start_response)
            
        except Exception as e:
            output_lines.append(f"<p class='error'>❌ WSGI failed: {e}</p>")
            output_lines.append(f"<pre>{traceback.format_exc()}</pre>")
            raise
            
    except Exception as e:
        output_lines.append(f"<div class='error'><h2>Fatal Error:</h2><pre>{traceback.format_exc()}</pre></div>")
    
    output_lines.append("</body></html>")
    output = '\n'.join(output_lines).encode('utf-8')
    
    status = '200 OK'
    response_headers = [
        ('Content-Type', 'text/html; charset=utf-8'),
        ('Content-Length', str(len(output)))
    ]
    start_response(status, response_headers)
    return [output]
