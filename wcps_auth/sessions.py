import asyncio
import uuid

class SessionManager:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance._user_sessions = {}
            cls._instance._server_sessions = {}
        return cls._instance

    async def authorize_user(self, user):
        async with self._lock:
            if user.username in self._user_sessions:
                return self._user_sessions[user.username]['session_id']

            session_id = str(uuid.uuid4())
            self._user_sessions[user.username] = {
                'user': user,
                'session_id': session_id
            }
            return session_id

    async def authorize_server(self, server):
        async with self._lock:
            if server.id in self._server_sessions:
                return self._server_sessions[server.id]['session_id']

            session_id = str(uuid.uuid4())
            self._server_sessions[server.id] = {
                'server': server,
                'session_id': session_id
            }
            return session_id

    async def is_user_authorized(self, username):
        async with self._lock:
            return username in self._user_sessions

    async def is_server_authorized(self, server_id):
        async with self._lock:
            return server_id in self._server_sessions

    async def unauthorize_user(self, username):
        async with self._lock:
            if username in self._user_sessions:
                del self._user_sessions[username]

    async def unauthorize_server(self, server_id):
        async with self._lock:
            if server_id in self._server_sessions:
                del self._server_sessions[server_id]

    def get_all_authorized_users(self):
        return list(self._user_sessions.values())

    def get_all_authorized_servers(self):
        return list(self._server_sessions.values())
