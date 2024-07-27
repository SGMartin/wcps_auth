import asyncio
import uuid

class SessionManager:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance._sessions = {}
            cls._instance._user_to_session = {}
            cls._instance._server_to_session = {}
        return cls._instance

    async def authenticate_player(self, user_id):
        async with self._lock:
            if user_id in self._user_to_session:
                return self._user_to_session[user_id]

            session_id = str(uuid.uuid4())
            self._user_to_session[user_id] = session_id
            self._sessions[session_id] = {'user_id': user_id}
            return session_id

    async def authenticate_server(self, server_id):
        async with self._lock:
            if server_id in self._server_to_session:
                return self._server_to_session[server_id]

            session_id = str(uuid.uuid4())
            self._server_to_session[server_id] = session_id
            self._sessions[session_id] = {'server_id': server_id}
            return session_id

    async def get_session_id_for_user(self, user_id):
        async with self._lock:
            return self._user_to_session.get(user_id)

    async def get_session_id_for_server(self, server_id):
        async with self._lock:
            return self._server_to_session.get(server_id)

    async def get_user_id_for_session(self, session_id):
        async with self._lock:
            session = self._sessions.get(session_id)
            return session.get('user_id') if session else None

    async def get_server_id_for_session(self, session_id):
        async with self._lock:
            session = self._sessions.get(session_id)
            return session.get('server_id') if session else None

    async def is_player_authenticated(self, user_id):
        async with self._lock:
            return user_id in self._user_to_session

    async def is_server_authenticated(self, server_id):
        async with self._lock:
            return server_id in self._server_to_session

    async def unauthorize_player(self, user_id):
        async with self._lock:
            session_id = self._user_to_session.pop(user_id, None)
            if session_id:
                self._sessions.pop(session_id, None)

    async def unauthorize_server(self, server_id):
        async with self._lock:
            session_id = self._server_to_session.pop(server_id, None)
            if session_id:
                self._sessions.pop(session_id, None)