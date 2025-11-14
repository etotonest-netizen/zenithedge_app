"""
WebSocket consumer for real-time notification delivery
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for delivering real-time notifications to users
    
    URL: ws://server/stream/insights/<user_id>/
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.user_group_name = f"user_{self.user_id}_notifications"
        
        # Verify user is authenticated
        user = self.scope.get('user')
        
        if not user or not user.is_authenticated:
            logger.warning(f"Unauthenticated connection attempt for user_id={self.user_id}")
            await self.close()
            return
        
        # Verify user can only connect to their own channel
        if str(user.id) != str(self.user_id):
            logger.warning(f"User {user.id} attempted to connect to user {self.user_id}'s channel")
            await self.close()
            return
        
        # Join user's personal notification group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"WebSocket connected: User {self.user_id} joined {self.user_group_name}")
        
        # Send unread notification count on connect
        unread_count = await self.get_unread_count(user)
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'unread_count': unread_count
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
            logger.info(f"WebSocket disconnected: User {self.user_id} left {self.user_group_name}")
    
    async def receive(self, text_data):
        """
        Handle messages received from WebSocket client
        
        Expected commands:
        - mark_read: {id: notification_id}
        - mark_all_read: {}
        - get_unread_count: {}
        """
        try:
            data = json.loads(text_data)
            command = data.get('command')
            
            user = self.scope.get('user')
            
            if command == 'mark_read':
                notification_id = data.get('id')
                if notification_id:
                    success = await self.mark_notification_read(notification_id, user)
                    await self.send(text_data=json.dumps({
                        'type': 'mark_read_response',
                        'success': success,
                        'notification_id': notification_id
                    }))
            
            elif command == 'mark_all_read':
                count = await self.mark_all_read(user)
                await self.send(text_data=json.dumps({
                    'type': 'mark_all_read_response',
                    'count': count
                }))
            
            elif command == 'get_unread_count':
                unread_count = await self.get_unread_count(user)
                await self.send(text_data=json.dumps({
                    'type': 'unread_count',
                    'count': unread_count
                }))
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received from user {self.user_id}")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
    
    async def notification_message(self, event):
        """
        Handle notification message from channel layer
        
        This is called when NotificationManager.deliver_websocket() sends a message
        """
        notification = event['notification']
        
        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'notification': notification
        }))
        
        logger.info(f"Sent notification #{notification['id']} to user {self.user_id}")
    
    # Database operations (must be wrapped in database_sync_to_async)
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id, user):
        """Mark a specific notification as read"""
        try:
            from .models import InsightNotification
            notification = InsightNotification.objects.get(id=notification_id, user=user)
            notification.mark_as_read()
            return True
        except InsightNotification.DoesNotExist:
            logger.warning(f"Notification {notification_id} not found for user {user.id}")
            return False
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False
    
    @database_sync_to_async
    def mark_all_read(self, user):
        """Mark all notifications as read for user"""
        try:
            from .manager import NotificationManager
            return NotificationManager.mark_all_as_read(user)
        except Exception as e:
            logger.error(f"Error marking all as read: {e}")
            return 0
    
    @database_sync_to_async
    def get_unread_count(self, user):
        """Get unread notification count for user"""
        try:
            from .manager import NotificationManager
            return NotificationManager.get_unread_count(user)
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return 0
