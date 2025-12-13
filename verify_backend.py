import unittest
import requests
import json
import os

BASE_URL = "http://localhost:8080"

class TestBackendAPI(unittest.TestCase):
    def test_01_homepage(self):
        """Test if homepage loads"""
        try:
            r = requests.get(BASE_URL + "/")
            self.assertEqual(r.status_code, 200)
            print("✅ Homepage is up")
        except requests.exceptions.ConnectionError:
            self.fail("Server is down")

    def test_02_list_photos(self):
        """Test photo listing"""
        r = requests.get(f"{BASE_URL}/api/list_photos")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIsInstance(data, list)
        print(f"✅ Listed {len(data)} photos")

    def test_03_config(self):
        """Test config read/write"""
        # Save
        new_conf = {"test_val": 123}
        r = requests.post(f"{BASE_URL}/api/save_config", json=new_conf)
        self.assertEqual(r.status_code, 200)
        
        # Read
        r = requests.get(f"{BASE_URL}/api/get_config")
        data = r.json()
        self.assertEqual(data.get('test_val'), 123)
        print("✅ Config Save/Load works")

    def test_04_delete_photos(self):
        """Test batch delete (safe mode)"""
        # Create dummy file to delete
        dummy = "test_delete_me.jpg"
        with open(f"my_frame_web/uploads/{dummy}", "w") as f:
            f.write("dummy")
            
        r = requests.post(f"{BASE_URL}/api/delete_photos", json={'filenames': [dummy]})
        self.assertEqual(r.status_code, 200)
        res = r.json()
        self.assertEqual(res['deleted'], 1)
        print("✅ Batch Delete works")

    def test_05_ai_generation_mock(self):
        """Mock test for AI Endpoint availability (not actual gen)"""
        # Just check if endpoint handles bad request correctly (proof of life)
        r = requests.post(f"{BASE_URL}/api/generate_ai", json={}) 
        # Should fail with 500 or error because prompt logic, but server should respond
        self.assertIn(r.status_code, [200, 500]) 
        print("✅ AI Endpoint is reachable")

if __name__ == '__main__':
    unittest.main()
