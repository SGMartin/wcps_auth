
import networking.users

class Session:
    def __init__(self, u):
        self.session_id = None
        self.user_id = u.username
        self.access_level = u.rights

class SessionManager:
    def __init__(self):
        self.sessions = {}

    def add(self, user) -> None:
        session_id = 0
        while True:
            session_id += 1
            if session_id not in self.sessions:
                break

        user.session_id = session_id
        self.sessions[session_id] = Session(user)

    def get(self, session_id) -> Session:
        return self.sessions.get(session_id)

    def remove(self, session_id) -> None:
        self.sessions.pop(session_id, None)

UserSessions = SessionManager()

def Authorize(user):
    # use the manager to add a new session for the user
    UserSessions.add(user)

def Remove(user):
    # use the manager to remove the session with the given session ID
    UserSessions.remove(user.session_id)

def GetAllAuthorized() -> list:
    return [session.user_id for session in UserSessions.sessions.values()]

def IsAuthorized(user) -> bool:
    return user.username in GetAllAuthorized()