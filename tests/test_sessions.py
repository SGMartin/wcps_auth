import unittest
import asyncio
from wcps_auth.sessions import SessionManager  # Ensure this matches the import path for your SessionManager

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
        user_id = 'user123'
        session_id = self.loop.run_until_complete(self.session_manager.authorize_player(user_id))
        self.assertIsNotNone(session_id)
        self.assertIn(user_id, self.loop.run_until_complete(self.session_manager.get_all_authorized_users()))

    def test_authorize_server(self):
        server_id = 'server123'
        session_id = self.loop.run_until_complete(self.session_manager.authorize_server(server_id))
        self.assertIsNotNone(session_id)
        self.assertIn(server_id, self.loop.run_until_complete(self.session_manager.get_all_authorized_servers()))

    def test_unauthorize_player(self):
        user_id = 'user123'
        self.loop.run_until_complete(self.session_manager.authorize_player(user_id))
        self.loop.run_until_complete(self.session_manager.unauthorize_player(user_id))
        self.assertNotIn(user_id, self.loop.run_until_complete(self.session_manager.get_all_authorized_users()))

    def test_unauthorize_server(self):
        server_id = 'server123'
        self.loop.run_until_complete(self.session_manager.authorize_server(server_id))
        self.loop.run_until_complete(self.session_manager.unauthorize_server(server_id))
        self.assertNotIn(server_id, self.loop.run_until_complete(self.session_manager.get_all_authorized_servers()))

    def test_get_session_id_for_user(self):
        user_id = 'user123'
        session_id = self.loop.run_until_complete(self.session_manager.authorize_player(user_id))
        fetched_session_id = self.loop.run_until_complete(self.session_manager.get_session_id_for_user(user_id))
        self.assertEqual(session_id, fetched_session_id)

    def test_get_session_id_for_server(self):
        server_id = 'server123'
        session_id = self.loop.run_until_complete(self.session_manager.authorize_server(server_id))
        fetched_session_id = self.loop.run_until_complete(self.session_manager.get_session_id_for_server(server_id))
        self.assertEqual(session_id, fetched_session_id)

    def test_get_user_id_for_session(self):
        user_id = 'user123'
        session_id = self.loop.run_until_complete(self.session_manager.authorize_player(user_id))
        fetched_user_id = self.loop.run_until_complete(self.session_manager.get_user_id_for_session(session_id))
        self.assertEqual(user_id, fetched_user_id)

    def test_get_server_id_for_session(self):
        server_id = 'server123'
        session_id = self.loop.run_until_complete(self.session_manager.authorize_server(server_id))
        fetched_server_id = self.loop.run_until_complete(self.session_manager.get_server_id_for_session(session_id))
        self.assertEqual(server_id, fetched_server_id)

    def test_is_player_authorized(self):
        user_id = 'user123'
        self.loop.run_until_complete(self.session_manager.authorize_player(user_id))
        is_authorized = self.loop.run_until_complete(self.session_manager.is_player_authorized(user_id))
        self.assertTrue(is_authorized)

    def test_is_server_authorized(self):
        server_id = 'server123'
        self.loop.run_until_complete(self.session_manager.authorize_server(server_id))
        is_authorized = self.loop.run_until_complete(self.session_manager.is_server_authorized(server_id))
        self.assertTrue(is_authorized)

    def test_get_authorized_player_count(self):
        user_ids = ['user123', 'user456', 'user789']
        for user_id in user_ids:
            self.loop.run_until_complete(self.session_manager.authorize_player(user_id))
        count = self.loop.run_until_complete(self.session_manager.get_authorized_player_count())
        self.assertEqual(count, len(user_ids))

    def test_get_authorized_server_count(self):
        server_ids = ['server123', 'server456', 'server789']
        for server_id in server_ids:
            self.loop.run_until_complete(self.session_manager.authorize_server(server_id))
        count = self.loop.run_until_complete(self.session_manager.get_authorized_server_count())
        self.assertEqual(count, len(server_ids))

if __name__ == '__main__':
    unittest.main()
