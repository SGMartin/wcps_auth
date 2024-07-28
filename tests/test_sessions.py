import unittest
import asyncio
from wcps_auth.sessions import SessionManager

class MockUser:
    def __init__(self, username):
        self.username = username

class MockServer:
    def __init__(self, server_id):
        self.id = server_id


class TestSessionManager(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.get_event_loop()
        self.session_manager = SessionManager()

    def tearDown(self):
        # Clear the singleton instance to ensure a fresh state for each test
        SessionManager._instance = None

    def test_singleton(self):
        another_instance = SessionManager()
        self.assertIs(self.session_manager, another_instance)

    def test_authorize_user(self):
        user = MockUser('user123')
        session_id = self.loop.run_until_complete(self.session_manager.authorize_user(user))
        self.assertIsNotNone(session_id)
        self.assertTrue(self.loop.run_until_complete(self.session_manager.is_user_authorized(user.username)))

    def test_authorize_server(self):
        server = MockServer(123)
        session_id = self.loop.run_until_complete(self.session_manager.authorize_server(server))
        self.assertIsNotNone(session_id)
        self.assertTrue(self.loop.run_until_complete(self.session_manager.is_server_authorized(server.id)))

    def test_unauthorize_user(self):
        user = MockUser('user123')
        self.loop.run_until_complete(self.session_manager.authorize_user(user))
        self.loop.run_until_complete(self.session_manager.unauthorize_user(user.username))
        self.assertFalse(self.loop.run_until_complete(self.session_manager.is_user_authorized(user.username)))

    def test_unauthorize_server(self):
        server = MockServer(123)
        self.loop.run_until_complete(self.session_manager.authorize_server(server))
        self.loop.run_until_complete(self.session_manager.unauthorize_server(server.id))
        self.assertFalse(self.loop.run_until_complete(self.session_manager.is_server_authorized(server.id)))

    def test_get_all_authorized_users(self):
        users = [MockUser('user123'), MockUser('user456')]
        for user in users:
            self.loop.run_until_complete(self.session_manager.authorize_user(user))
        authorized_users = self.session_manager.get_all_authorized_users()
        self.assertEqual(len(authorized_users), len(users))

    def test_get_all_authorized_servers(self):
        servers = [MockServer(123), MockServer(456)]
        for server in servers:
            self.loop.run_until_complete(self.session_manager.authorize_server(server))
        authorized_servers = self.session_manager.get_all_authorized_servers()
        self.assertEqual(len(authorized_servers), len(servers))

if __name__ == '__main__':
    unittest.main()
