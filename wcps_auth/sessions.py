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
            cls._instance._user_session_id_counter = (
                0  # Initialize counter within the allowed range
            )
        return cls._instance

    async def authorize_user(self, user):
        async with self._lock:
            if user.username in self._user_sessions:
                return self._user_sessions[user.username]["session_id"]

            if (
                len(self._user_sessions) >= 32768
            ):  # Check if all possible session IDs are used
                raise Exception("No available session IDs for users")

            # Generate a new session ID within the range [0, 32767]
            session_id = self._generate_user_session_id()
            self._user_sessions[user.username] = {
                "user": user,
                "session_id": session_id,
                "is_activated": False,
                "game_server": None
            }
            return session_id

    def _generate_user_session_id(self):
        used_ids = {session["session_id"] for session in self._user_sessions.values()}
        for _ in range(
            32768
        ):  # 32768 is the total number of unique session IDs available
            self._user_session_id_counter += 1
            if self._user_session_id_counter > 32767:
                self._user_session_id_counter = 0

            if self._user_session_id_counter not in used_ids:
                return self._user_session_id_counter

        raise Exception("No available session IDs for users")

    async def authorize_server(self, server):
        async with self._lock:
            if server.id in self._server_sessions:
                return self._server_sessions[server.id]["session_id"]

            session_id = str(uuid.uuid4())
            self._server_sessions[server.id] = {
                "server": server,
                "session_id": session_id,
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
            server_session = self._server_sessions.get(server_id)
            session_id = server_session["session_id"]
            # Remove the server session from _server_sessions
            if server_id in self._server_sessions:
                del self._server_sessions[server_id]

            # Remove all user sessions associated with this server_id
            users_to_remove = [
                username
                for username, session in self._user_sessions.items()
                if session.get("game_server") == session_id
                ]

        for username in users_to_remove:
            del self._user_sessions[username]

    def get_all_authorized_users(self):
        return list(self._user_sessions.values())

    def get_all_authorized_servers(self):
        return list(self._server_sessions.values())

    async def get_user_session_id(self, username):
        async with self._lock:
            if username in self._user_sessions:
                return self._user_sessions[username]["session_id"]
            else:
                return None

    async def get_user_by_session_id(self, session_id):
        async with self._lock:
            for session in self._user_sessions.values():
                if session["session_id"] == session_id:
                    return session["user"]
            return None

    async def activate_user_session(self, session_id, game_server_id):
        async with self._lock:
            for session in self._user_sessions.values():
                if session["session_id"] == session_id:
                    session["is_activated"] = True
                    session["game_server"] = game_server_id
                    return True
            return False

    async def is_user_session_activated(self, session_id):
        async with self._lock:
            for session in self._user_sessions.values():
                if session["session_id"] == session_id:
                    return session["is_activated"]
            return False
