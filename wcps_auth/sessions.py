import asyncio
import threading
import logging

# Ensure logging configuration is in place
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Session:
    def __init__(self, entity):
        self.session_id = None
        self.entity_id = entity.username if hasattr(entity, 'username') else entity.id
        self.access_level = entity.rights if hasattr(entity, 'rights') else entity.access_level

class SessionManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance.sessions = {}
            cls._instance._lock = threading.Lock()  # Add a lock for thread safety
        return cls._instance

    def add(self, entity) -> None:
        with self._lock:
            if hasattr(entity, 'session_id') and entity.session_id in self.sessions:
                logging.warning(f"Session already exists for entity with ID {entity.session_id}")
                return

            session_id = 0
            while session_id in self.sessions:
                session_id += 1

            entity.session_id = session_id
            self.sessions[session_id] = Session(entity)
            logging.info(f"Added session {session_id} for entity with ID {entity.session_id}")

    def get(self, session_id) -> Session:
        with self._lock:
            return self.sessions.get(session_id)

    def remove(self, session_id) -> None:
        with self._lock:
            if session_id in self.sessions:
                self.sessions.pop(session_id)
                logging.info(f"Removed session {session_id}")
            else:
                logging.warning(f"Session ID {session_id} not found")

    def get_all_authorized(self) -> list:
        with self._lock:
            return [session.entity_id for session in self.sessions.values()]

    def is_authorized(self, entity) -> bool:
        with self._lock:
            return entity.session_id in self.sessions

UserSessions = SessionManager()

async def async_authorize(entity):
    await asyncio.sleep(0)  # Simulate async operation
    UserSessions.add(entity)

async def async_remove(entity):
    await asyncio.sleep(0)  # Simulate async operation
    UserSessions.remove(entity.session_id)