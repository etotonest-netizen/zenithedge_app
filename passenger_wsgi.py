"""
Passenger WSGI Configuration for cPanel Shared Hosting

This file is used by Passenger (mod_passenger) to run Django on shared hosting.
It automatically detects the project root and configures all import paths.

Deployment on cPanel:
1. Upload project to: /home/username/zenithedge_trading_hub/
2. Setup Python App in cPanel:
   - Python Version: 3.9+
   - Application Root: /home/equabish/zenithedge_trading_hub
   - Application URL: etotonest.com (or z.equatorfoods.org)
   - Application Startup File: passenger_wsgi.py
   - Application Entry Point: application
3. Install dependencies via SSH or cPanel terminal
4. Run migrations
5. Restart application

Environment Variables to Set in cPanel:
- DJANGO_SETTINGS_MODULE=zenithedge.settings_production
- DJANGO_SECRET_KEY=(generate with: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
- DB_NAME=your_database_name
- DB_USER=your_database_user
- DB_PASSWORD=your_database_password
- DB_HOST=localhost
- WEBHOOK_TOKEN=your_secure_webhook_token
"""

import sys
import os
from pathlib import Path

# Detect project root automatically
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = CURRENT_DIR

# Add project root to Python path
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Add parent directory (if running from subdirectory)
PARENT_DIR = os.path.dirname(PROJECT_ROOT)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

# Set Django settings module
# Try production settings first, fall back to default
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    # Check if production settings exist
    production_settings_path = os.path.join(PROJECT_ROOT, 'zenithedge', 'settings_production.py')
    if os.path.exists(production_settings_path):
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings_production')
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')

# Import Django WSGI application
try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    
    # Log successful startup (optional)
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [PASSENGER] %(levelname)s: %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Django application loaded successfully")
    logger.info(f"Project root: {PROJECT_ROOT}")
    logger.info(f"Python path: {sys.path[:3]}")
    logger.info(f"Settings module: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    
except Exception as e:
    # If Django fails to load, create a simple error page
    import logging
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s [PASSENGER-ERROR] %(levelname)s: %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to load Django application: {e}", exc_info=True)
    
    # Create a simple error application
    def application(environ, start_response):
        """Fallback error page if Django fails to load"""
        status = '500 Internal Server Error'
        output = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Application Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .error {{ background: #fee; border: 1px solid #fcc; padding: 20px; border-radius: 5px; }}
                code {{ background: #f5f5f5; padding: 2px 5px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <h1>🚨 Application Error</h1>
            <div class="error">
                <h2>Django Failed to Load</h2>
                <p><strong>Error:</strong> {str(e)}</p>
                <h3>Troubleshooting Steps:</h3>
                <ol>
                    <li>Check that all dependencies are installed: <code>pip install -r requirements.txt</code></li>
                    <li>Verify database credentials in environment variables</li>
                    <li>Run migrations: <code>python manage.py migrate</code></li>
                    <li>Check Python version (requires 3.9+)</li>
                    <li>Review error logs in cPanel or via SSH</li>
                </ol>
                <h3>Environment:</h3>
                <ul>
                    <li>Project Root: <code>{PROJECT_ROOT}</code></li>
                    <li>Settings Module: <code>{os.environ.get('DJANGO_SETTINGS_MODULE', 'NOT SET')}</code></li>
                    <li>Python Path: <code>{sys.path[:3]}</code></li>
                </ul>
            </div>
        </body>
        </html>
        """.encode('utf-8')
        
        response_headers = [
            ('Content-Type', 'text/html; charset=utf-8'),
            ('Content-Length', str(len(output)))
        ]
        start_response(status, response_headers)
        return [output]

# Passenger requires the 'application' callable
# It's already defined above in both success and error cases
