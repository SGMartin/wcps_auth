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
            cls._instance._authorized_users = set()
            cls._instance._authorized_servers = set()
        return cls._instance

    async def authorize_player(self, user):
        async with self._lock:
            if user in self._user_to_session:
                return self._user_to_session[user]

            session_id = str(uuid.uuid4())
            self._user_to_session[user] = session_id
            self._sessions[session_id] = {'user': user}
            self._authorized_users.add(user)
            return session_id

    async def authorize_server(self, server):
        async with self._lock:
            if server in self._server_to_session:
                return self._server_to_session[server]

            session_id = str(uuid.uuid4())
            self._server_to_session[server] = session_id
            self._sessions[session_id] = {'server': server}
            self._authorized_servers.add(server)
            return session_id

    async def get_session_id_for_user(self, user):
        async with self._lock:
            return self._user_to_session.get(user)

    async def get_session_id_for_server(self, server):
        async with self._lock:
            return self._server_to_session.get(server)

    async def get_user_for_session(self, session_id):
        async with self._lock:
            session = self._sessions.get(session_id)
            return session.get('user') if session else None

    async def get_server_for_session(self, session_id):
        async with self._lock:
            session = self._sessions.get(session_id)
            return session.get('server') if session else None

    async def is_player_authorized(self, user):
        async with self._lock:
            return user in self._user_to_session

    async def is_server_authorized(self, server):
        async with self._lock:
            return server in self._server_to_session

    async def unauthorize_player(self, user):
        async with self._lock:
            session_id = self._user_to_session.pop(user, None)
            if session_id:
                self._sessions.pop(session_id, None)
                self._authorized_users.discard(user)

    async def unauthorize_server(self, server):
        async with self._lock:
            session_id = self._server_to_session.pop(server, None)
            if session_id:
                self._sessions.pop(session_id, None)
                self._authorized_servers.discard(server)

    async def get_authorized_player_count(self):
        async with self._lock:
            return len(self._user_to_session)

    async def get_authorized_server_count(self):
        async with self._lock:
            return len(self._server_to_session)

    def get_all_authorized_users(self):
        return list(self._authorized_users)

    def get_all_authorized_servers(self):
        return list(self._authorized_servers)
