import unittest
import asyncio
from wcps_auth.sessions import SessionManager

class MockUser:
    def __init__(self, user_id):
        self.user_id = user_id

class MockServer:
    def __init__(self, server_id):
        self.server_id = server_id

class TestSessionManager(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.get_event_loop()
        self.session_manager = SessionManager()

    def tearDown(self):
        SessionManager._instance = None

    def test_singleton(self):
        another_instance = SessionManager()
        self.assertIs(self.session_manager, another_instance)

    def test_authorize_player(self):
        user = MockUser('user123')
        session_id = self.loop.run_until_complete(self.session_manager.authorize_player(user))
        self.assertIsNotNone(session_id)
        self.assertIn(user, self.session_manager.get_all_authorized_users())

    def test_authorize_server(self):
        server = MockServer('server123')
        session_id = self.loop.run_until_complete(self.session_manager.authorize_server(server))
        self.assertIsNotNone(session_id)
        self.assertIn(server, self.session_manager.get_all_authorized_servers())

    def test_unauthorize_player(self):
        user = MockUser('user123')
        self.loop.run_until_complete(self.session_manager.authorize_player(user))
        self.loop.run_until_complete(self.session_manager.unauthorize_player(user))
        self.assertNotIn(user, self.session_manager.get_all_authorized_users())

    def test_unauthorize_server(self):
        server = MockServer('server123')
        self.loop.run_until_complete(self.session_manager.authorize_server(server))
        self.loop.run_until_complete(self.session_manager.unauthorize_server(server))
        self.assertNotIn(server, self.session_manager.get_all_authorized_servers())

    def test_get_session_id_for_user(self):
        user = MockUser('user123')
        session_id = self.loop.run_until_complete(self.session_manager.authorize_player(user))
        fetched_session_id = self.loop.run_until_complete(self.session_manager.get_session_id_for_user(user))
        self.assertEqual(session_id, fetched_session_id)

    def test_get_session_id_for_server(self):
        server = MockServer('server123')
        session_id = self.loop.run_until_complete(self.session_manager.authorize_server(server))
        fetched_session_id = self.loop.run_until_complete(self.session_manager.get_session_id_for_server(server))
        self.assertEqual(session_id, fetched_session_id)

    def test_get_user_for_session(self):
        user = MockUser('user123')
        session_id = self.loop.run_until_complete(self.session_manager.authorize_player(user))
        fetched_user = self.loop.run_until_complete(self.session_manager.get_user_for_session(session_id))
        self.assertEqual(user, fetched_user)

    def test_get_server_for_session(self):
        server = MockServer('server123')
        session_id = self.loop.run_until_complete(self.session_manager.authorize_server(server))
        fetched_server = self.loop.run_until_complete(self.session_manager.get_server_for_session(session_id))
        self.assertEqual(server, fetched_server)

    def test_is_player_authorized(self):
        user = MockUser('user123')
        self.loop.run_until_complete(self.session_manager.authorize_player(user))
        is_authorized = self.loop.run_until_complete(self.session_manager.is_player_authorized(user))
        self.assertTrue(is_authorized)

    def test_is_server_authorized(self):
        server = MockServer('server123')
        self.loop.run_until_complete(self.session_manager.authorize_server(server))
        is_authorized = self.loop.run_until_complete(self.session_manager.is_server_authorized(server))
        self.assertTrue(is_authorized)

    def test_get_authorized_player_count(self):
        users = [MockUser('user123'), MockUser('user456'), MockUser('user789')]
        for user in users:
            self.loop.run_until_complete(self.session_manager.authorize_player(user))
        count = self.loop.run_until_complete(self.session_manager.get_authorized_player_count())
        self.assertEqual(count, len(users))

    def test_get_authorized_server_count(self):
        servers = [MockServer('server123'), MockServer('server456'), MockServer('server789')]
        for server in servers:
            self.loop.run_until_complete(self.session_manager.authorize_server(server))
        count = self.loop.run_until_complete(self.session_manager.get_authorized_server_count())
        self.assertEqual(count, len(servers))

if __name__ == '__main__':
    unittest.main()
