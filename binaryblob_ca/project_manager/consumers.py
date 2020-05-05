import json
from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.auth import login, logout
from channels.exceptions import StopConsumer
from channels.generic.websocket import WebsocketConsumer
from django.utils.timezone import now

from .models import ChatLogModel

# This is so bad, don't do this
LOGS = []


def add_log(msg_dict):
    ChatLogModel().log(msg_dict)


class ChatConsumer(WebsocketConsumer):
    global LOGS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = None
        self.room_group_name = "ERROR"
        self.user = self.scope['user']
        self.logs = []

    def connect(self):
        if not self.user or not self.user.is_authenticated:
            raise StopConsumer("User was not logged in")
        login(self.scope, self.user)
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.user = self.scope['user'].username
        if not self.room_name:
            logout(self.scope)
            raise StopConsumer("No room name was selected")
        self.room_group_name = 'chat_%s' % self.room_name
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()
        for log in ChatLogModel.objects.filter(timestamp__gte=now() - timedelta(days=1)):
            if log.group_name == self.room_group_name:
                event = {'user': log.user.username, 'message': log.message, 'timestamp': str(log.timestamp)}
                self.chat_message(event)

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
        logout(self.scope)
        raise StopConsumer("Disconnected")

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        event = {
            'group_name': self.room_group_name,
            'type': 'chat_message',
            'user': self.user,
            'message': message,
            'timestamp': str(now())
        }
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            event
        )
        add_log(event)

    def chat_message(self, event):
        user = event['user']
        message = event['message']
        time = event['timestamp']
        self.send(text_data=json.dumps({'timestamp': time, 'user': user, 'message': message}))
