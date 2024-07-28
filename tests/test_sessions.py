import unittest
import asyncio
from wcps_auth.sessions import SessionManager  # Adjust the import if needed

class TestSessionManager(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        """Set up the test case environment."""
        self.manager = SessionManager()
        await self._reset_manager()

    async def _reset_manager(self):
        async with self.manager._lock:
            self.manager._sessions.clear()
            self.manager._user_to_session.clear()
            self.manager._server_to_session.clear()

    async def test_authenticate_player(self):
        user_id = "player123"
        session_id = await self.manager.authenticate_player(user_id)
        self.assertIsInstance(session_id, str)
        self.assertTrue(session_id)
        self.assertEqual(await self.manager.get_session_id_for_user(user_id), session_id)

    async def test_authenticate_server(self):
        server_id = "server456"
        session_id = await self.manager.authenticate_server(server_id)
        self.assertIsInstance(session_id, str)
        self.assertTrue(session_id)
        self.assertEqual(await self.manager.get_session_id_for_server(server_id), session_id)

    async def test_is_player_authenticated(self):
        user_id = "player789"
        self.assertFalse(await self.manager.is_player_authenticated(user_id))
        await self.manager.authenticate_player(user_id)
        self.assertTrue(await self.manager.is_player_authenticated(user_id))

    async def test_is_server_authenticated(self):
        server_id = "server012"
        self.assertFalse(await self.manager.is_server_authenticated(server_id))
        await self.manager.authenticate_server(server_id)
        self.assertTrue(await self.manager.is_server_authenticated(server_id))

    async def test_get_user_id_for_session(self):
        user_id = "playerabc"
        session_id = await self.manager.authenticate_player(user_id)
        retrieved_user_id = await self.manager.get_user_id_for_session(session_id)
        self.assertEqual(user_id, retrieved_user_id)

    async def test_get_server_id_for_session(self):
        server_id = "serverdef"
        session_id = await self.manager.authenticate_server(server_id)
        retrieved_server_id = await self.manager.get_server_id_for_session(session_id)
        self.assertEqual(server_id, retrieved_server_id)

    async def test_authenticate_existing_player(self):
        user_id = "player1234"
        first_session_id = await self.manager.authenticate_player(user_id)
        second_session_id = await self.manager.authenticate_player(user_id)
        self.assertEqual(first_session_id, second_session_id)

    async def test_authenticate_existing_server(self):
        server_id = "server5678"
        first_session_id = await self.manager.authenticate_server(server_id)
        second_session_id = await self.manager.authenticate_server(server_id)
        self.assertEqual(first_session_id, second_session_id)

    async def test_get_authorized_player_count(self):
        user_id = "player123"
        await self.manager.authenticate_player(user_id)
        count = await self.manager.get_authorized_player_count()
        self.assertEqual(count, 1)
        await self.manager.unauthorize_player(user_id)
        count = await self.manager.get_authorized_player_count()
        self.assertEqual(count, 0)

    async def test_get_authorized_server_count(self):
        server_id = "server456"
        await self.manager.authenticate_server(server_id)
        count = await self.manager.get_authorized_server_count()
        self.assertEqual(count, 1)
        await self.manager.unauthorize_server(server_id)
        count = await self.manager.get_authorized_server_count()
        self.assertEqual(count, 0)

if __name__ == "__main__":
    unittest.main()
