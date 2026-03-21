import unittest
from fastapi.testclient import TestClient

from main import app


class ApiSmokeTests(unittest.TestCase):
    def test_health_endpoint(self):
        client = TestClient(app)
        response = client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        self.assertIn('status', response.json())


if __name__ == '__main__':
    unittest.main()
