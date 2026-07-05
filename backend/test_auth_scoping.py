import os
import sys
import unittest
from unittest.mock import patch
import pandas as pd
from fastapi import Depends, HTTPException
from fastapi.testclient import TestClient
from fastapi.security import HTTPAuthorizationCredentials
from typing import Optional

# Adjust path to import backend modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.database import Base, get_db
from app.dependencies.auth import get_current_user_id, security
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup test SQLite DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Database dependency override
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Auth mock control flags
auth_enabled = False

def mock_get_current_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    if auth_enabled:
        if not credentials:
            raise HTTPException(status_code=401, detail="Authentication credentials are required.")
        token = credentials.credentials
        if token == "token-A":
            return "user-A"
        elif token == "token-B":
            return "user-B"
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    return None

app.dependency_overrides[get_current_user_id] = mock_get_current_user_id

client = TestClient(app)

class TestAuthScoping(unittest.TestCase):
    def setUp(self):
        # Create fresh tables for each test run
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def tearDown(self):
        # Clean up database
        Base.metadata.drop_all(bind=engine)
        if os.path.exists("test_auth.db"):
            try:
                os.remove("test_auth.db")
            except PermissionError:
                pass

    @patch("app.services.storage_service.StorageService.save_dataframe")
    @patch("app.services.storage_service.StorageService.load_dataframe")
    def test_local_dev_mode_no_auth(self, mock_load, mock_save):
        global auth_enabled
        auth_enabled = False
        
        # Mock dataframe saving/loading to avoid files on disk
        mock_save.return_value = ("storage/dataset_test_v1.csv", 100)
        mock_load.return_value = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})

        # Test upload without headers (should succeed in local-dev mode)
        csv_data = "col1,col2\n1,4\n2,5\n3,6"
        response = client.post(
            "/api/datasets/upload",
            files={"file": ("test.csv", csv_data, "text/csv")}
        )
        self.assertEqual(response.status_code, 200)
        dataset_id = response.json()["dataset_id"]
        
        # Test listing datasets
        list_response = client.get("/api/datasets")
        self.assertEqual(list_response.status_code, 200)
        datasets = list_response.json()
        self.assertEqual(len(datasets), 1)
        self.assertEqual(datasets[0]["id"], dataset_id)

    @patch("app.services.storage_service.StorageService.save_dataframe")
    @patch("app.services.storage_service.StorageService.load_dataframe")
    def test_authenticated_mode_isolation(self, mock_load, mock_save):
        global auth_enabled
        auth_enabled = True

        mock_save.return_value = ("storage/dataset_test_v1.csv", 100)
        mock_load.return_value = pd.DataFrame({"col1": [1, 2, 3]})

        csv_data = "col1\n1\n2\n3"

        # 1. Try uploading without headers (should fail with 401)
        response = client.post(
            "/api/datasets/upload",
            files={"file": ("test.csv", csv_data, "text/csv")}
        )
        self.assertEqual(response.status_code, 401)

        # 2. Upload dataset as User A
        res_a = client.post(
            "/api/datasets/upload",
            files={"file": ("user_a_file.csv", csv_data, "text/csv")},
            headers={"Authorization": "Bearer token-A"}
        )
        self.assertEqual(res_a.status_code, 200)
        dataset_a_id = res_a.json()["dataset_id"]

        # 3. Upload dataset as User B
        res_b = client.post(
            "/api/datasets/upload",
            files={"file": ("user_b_file.csv", csv_data, "text/csv")},
            headers={"Authorization": "Bearer token-B"}
        )
        self.assertEqual(res_b.status_code, 200)
        dataset_b_id = res_b.json()["dataset_id"]

        # 4. List datasets as User A (should only see User A's dataset)
        list_a = client.get("/api/datasets", headers={"Authorization": "Bearer token-A"})
        self.assertEqual(list_a.status_code, 200)
        datasets_a = list_a.json()
        self.assertEqual(len(datasets_a), 1)
        self.assertEqual(datasets_a[0]["id"], dataset_a_id)

        # 5. List datasets as User B (should only see User B's dataset)
        list_b = client.get("/api/datasets", headers={"Authorization": "Bearer token-B"})
        self.assertEqual(list_b.status_code, 200)
        datasets_b = list_b.json()
        self.assertEqual(len(datasets_b), 1)
        self.assertEqual(datasets_b[0]["id"], dataset_b_id)

        # 6. Try retrieving User A's dataset as User B (should return 404)
        get_fail = client.get(f"/api/datasets/{dataset_a_id}", headers={"Authorization": "Bearer token-B"})
        self.assertEqual(get_fail.status_code, 404)

        # 7. Try deleting User A's dataset as User B (should return 404)
        del_fail = client.delete(f"/api/datasets/{dataset_a_id}", headers={"Authorization": "Bearer token-B"})
        self.assertEqual(del_fail.status_code, 404)

        # 8. Get User A's dataset as User A (should succeed)
        get_ok = client.get(f"/api/datasets/{dataset_a_id}", headers={"Authorization": "Bearer token-A"})
        self.assertEqual(get_ok.status_code, 200)
        self.assertEqual(get_ok.json()["id"], dataset_a_id)

        # 9. Delete User A's dataset as User A (should succeed)
        del_ok = client.delete(f"/api/datasets/{dataset_a_id}", headers={"Authorization": "Bearer token-A"})
        self.assertEqual(del_ok.status_code, 200)

if __name__ == "__main__":
    unittest.main()
