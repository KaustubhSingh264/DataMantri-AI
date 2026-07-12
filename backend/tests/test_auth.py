import tempfile
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.db import Base
from app.models import subscription, upload_history, user
from app.routes import auth


class AuthFlowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db")
        self.engine = create_engine(
            f"sqlite:///{self.tmp.name}",
            connect_args={"check_same_thread": False},
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        auth.AUTH_RATE_LIMITS.clear()
        self.sent_links = []
        self.original_send = auth.send_password_reset_email
        self.original_support_send = auth.send_support_email
        self.original_support_email = auth.SUPPORT_EMAIL
        auth.SUPPORT_EMAIL = "support@example.com"
        auth.send_password_reset_email = self.capture_reset_link

        app = FastAPI()
        app.include_router(auth.router)

        def override_db():
            db = self.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[auth.get_db] = override_db
        self.client = TestClient(app)

    def tearDown(self):
        auth.send_password_reset_email = self.original_send
        auth.send_support_email = self.original_support_send
        auth.SUPPORT_EMAIL = self.original_support_email
        self.engine.dispose()
        self.tmp.close()

    def capture_reset_link(self, to_email, reset_url):
        self.sent_links.append((to_email, reset_url))
        return True

    def signup(self, email="user@example.com", password="StrongPass1!", username="datamantri"):
        return self.client.post(
            "/signup",
            json={"email": email, "username": username, "password": password},
        )

    def test_valid_registration_and_duplicate_checks(self):
        response = self.signup(email="User@Example.com", username="DataMantri")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Account created successfully.")

        duplicate_email = self.signup(email="user@example.com", username="newname")
        self.assertEqual(duplicate_email.status_code, 409)
        self.assertEqual(duplicate_email.json()["detail"], "This email is already registered.")

        duplicate_username = self.signup(email="second@example.com", username="datamantri")
        self.assertEqual(duplicate_username.status_code, 409)
        self.assertEqual(duplicate_username.json()["detail"], "This username is already taken.")

    def test_signup_rejects_short_password(self):
        response = self.signup(password="short")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Password must contain at least 8 characters.")

    def test_login_success_incorrect_password_and_missing_account(self):
        self.signup(email="login@example.com", username="loginuser", password="StrongPass1!")

        ok = self.client.post("/login", json={"email": "login@example.com", "password": "StrongPass1!"})
        self.assertEqual(ok.status_code, 200)
        self.assertIn("access_token", ok.json())

        username_login = self.client.post("/login", json={"email": "loginuser", "password": "StrongPass1!"})
        self.assertEqual(username_login.status_code, 200)

        wrong_password = self.client.post("/login", json={"email": "login@example.com", "password": "WrongPass1!"})
        self.assertEqual(wrong_password.status_code, 401)
        self.assertEqual(wrong_password.json()["detail"], "Incorrect password.")

        missing = self.client.post("/login", json={"email": "missing@example.com", "password": "StrongPass1!"})
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.json()["detail"], "Account not found.")

    def test_password_reset_token_updates_password_and_is_one_time_use(self):
        self.signup(email="reset@example.com", username="resetuser", password="OldPass123!")

        forgot = self.client.post("/forgot-password", json={"email": "reset@example.com"})
        self.assertEqual(forgot.status_code, 200)
        self.assertEqual(len(self.sent_links), 1)

        reset_url = self.sent_links[0][1]
        token = reset_url.split("token=", 1)[1].split("&", 1)[0]

        reset = self.client.post(
            "/reset-password",
            json={"email": "reset@example.com", "token": token, "new_password": "NewPass123!"},
        )
        self.assertEqual(reset.status_code, 200)

        login = self.client.post("/login", json={"email": "reset@example.com", "password": "NewPass123!"})
        self.assertEqual(login.status_code, 200)

        reused = self.client.post(
            "/reset-password",
            json={"email": "reset@example.com", "token": token, "new_password": "Another123!"},
        )
        self.assertEqual(reused.status_code, 400)
        self.assertEqual(reused.json()["detail"], "This reset link has expired.")

    def test_support_ticket_returns_success_only_after_email_send(self):
        self.signup(email="supporter@example.com", username="supporter", password="StrongPass1!")
        login = self.client.post("/login", json={"email": "supporter@example.com", "password": "StrongPass1!"})
        token = login.json()["access_token"]
        auth.send_support_email = lambda ticket, user: True

        response = self.client.post(
            "/support",
            json={"subject": "Upload issue", "message": "My CSV upload is failing."},
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["email_sent"])
        self.assertTrue(response.json()["ticket"]["email_sent"])

    def test_support_ticket_is_saved_and_returns_error_when_email_fails(self):
        self.signup(email="failure@example.com", username="failureuser", password="StrongPass1!")
        login = self.client.post("/login", json={"email": "failure@example.com", "password": "StrongPass1!"})
        token = login.json()["access_token"]

        def fail_email(ticket, user):
            raise RuntimeError("SMTP authentication failed")

        auth.send_support_email = fail_email
        response = self.client.post(
            "/support",
            json={"subject": "Billing issue", "message": "Payment did not update my plan."},
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(response.status_code, 502)
        self.assertIn("was saved", response.json()["detail"])
        tickets = self.client.get("/support/my", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(len(tickets.json()["tickets"]), 1)
        self.assertFalse(tickets.json()["tickets"][0]["email_sent"])


if __name__ == "__main__":
    unittest.main()
