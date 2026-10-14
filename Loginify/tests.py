import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import UserDetails

User = get_user_model()


class LoginSystemTests(TestCase):
    def test_required_model_fields_match_assignment(self):
        username = UserDetails._meta.get_field("username")
        email = UserDetails._meta.get_field("email")
        password = UserDetails._meta.get_field("password")
        self.assertEqual((username.max_length, username.primary_key), (50, True))
        self.assertEqual(email.unique, True)
        self.assertEqual((password.max_length, password.blank), (12, True))

    def test_hello_endpoint_has_exact_text(self):
        response = self.client.get(reverse("hello"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Hello, world!")

    def test_signup_creates_linked_profile_and_redirects_to_login(self):
        response = self.client.post(
            reverse("signup"),
            {
                "name": "Maya",
                "email": "maya@example.test",
                "password": "Strong-Maya-Password-482!",
            },
        )
        self.assertRedirects(response, "/login/?registered=1")
        user = User.objects.get(email="maya@example.test")
        profile = UserDetails.objects.get(username="Maya")
        self.assertEqual(profile.related_user, user)
        self.assertTrue(user.check_password("Strong-Maya-Password-482!"))
        self.assertEqual(profile.password, "")
        self.assertContains(self.client.get(response.url), "Account created")

    def test_signup_reports_missing_invalid_duplicate_email_and_username(self):
        first_payload = {
            "name": "Maya",
            "email": "maya@example.test",
            "password": "Strong-Maya-Password-482!",
        }
        self.client.post(reverse("signup"), first_payload)

        missing = self.client.post(reverse("signup"), {})
        self.assertEqual(missing.status_code, 200)
        self.assertContains(missing, "This field is required.")

        invalid_email = self.client.post(
            reverse("signup"),
            {**first_payload, "name": "No Email", "email": "not-an-email"},
        )
        self.assertContains(invalid_email, "Enter a valid email address.")

        duplicate_email = self.client.post(
            reverse("signup"),
            {**first_payload, "name": "Other Name"},
        )
        self.assertContains(duplicate_email, "already exists")

        duplicate_name = self.client.post(
            reverse("signup"),
            {**first_payload, "email": "other@example.test"},
        )
        self.assertContains(duplicate_name, "username is already taken")

    def test_signup_rejects_weak_password_without_saving_it(self):
        response = self.client.post(
            reverse("signup"),
            {"name": "Weak", "email": "weak@example.test", "password": "12345678"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="weak@example.test").exists())

    def test_login_success_and_wrong_credentials(self):
        user = User.objects.create_user(
            username="login@example.test",
            email="login@example.test",
            password="Valid-Login-Password-482!",
        )
        UserDetails.objects.create(
            username="Login User", email=user.email, related_user=user
        )
        bad_response = self.client.post(
            reverse("login"),
            {"email": user.email, "password": "wrong-password"},
        )
        self.assertContains(bad_response, "email or password is incorrect")

        good_response = self.client.post(
            reverse("login"),
            {"email": user.email, "password": "Valid-Login-Password-482!"},
        )
        self.assertRedirects(good_response, reverse("success"))
        self.assertContains(self.client.get(reverse("success")), "Login successful")

    def test_admin_can_see_userdetails_in_admin(self):
        staff = User.objects.create_superuser(
            username="admin@example.test",
            email="admin@example.test",
            password="Valid-Admin-Password-482!",
        )
        self.client.force_login(staff)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "User details")


class UserDetailsApiTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="staff@example.test",
            email="staff@example.test",
            password="Staff-Access-Password-482!",
            is_staff=True,
        )
        self.first_user = User.objects.create_user(
            username="first@example.test",
            email="first@example.test",
            password="First-User-Password-482!",
        )
        self.first_profile = UserDetails.objects.create(
            username="First User",
            email="first@example.test",
            related_user=self.first_user,
        )
        self.second_user = User.objects.create_user(
            username="second@example.test",
            email="second@example.test",
            password="Second-User-Password-482!",
        )
        self.second_profile = UserDetails.objects.create(
            username="Second User",
            email="second@example.test",
            related_user=self.second_user,
        )
        self.client.force_login(self.staff)

    def test_api_requires_authentication_and_staff_access(self):
        anonymous_client = Client()
        response = anonymous_client.get(reverse("api-users"))
        self.assertEqual(response.status_code, 401)
        ordinary_client = Client()
        ordinary_client.force_login(self.first_user)
        response = ordinary_client.get(reverse("api-users"))
        self.assertEqual(response.status_code, 403)

    def test_list_and_single_lookup_never_return_passwords(self):
        response = self.client.get(reverse("api-users"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["users"]), 2)
        self.assertNotIn("password", response.content.decode().lower())
        self.assertNotIn(self.first_user.password, response.content.decode())

        response = self.client.get(
            reverse("api-user-detail", args=[self.first_profile.email])
        )
        self.assertEqual(response.json()["user"]["username"], "First User")

    def test_single_lookup_returns_not_found(self):
        response = self.client.get(
            reverse("api-user-detail", args=["missing@example.test"])
        )
        self.assertEqual(response.status_code, 404)

    def test_update_changes_profile_and_auth_email(self):
        response = self.client.patch(
            reverse("api-user-update", args=[self.first_profile.email]),
            data=json.dumps({"name": "Renamed User", "email": "renamed@example.test"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"], {
            "username": "Renamed User", "email": "renamed@example.test"
        })
        self.first_user.refresh_from_db()
        self.assertEqual(self.first_user.email, "renamed@example.test")
        self.assertEqual(self.first_user.username, "renamed@example.test")

    def test_update_validates_json_email_and_duplicate_values(self):
        url = reverse("api-user-update", args=[self.first_profile.email])
        malformed = self.client.put(url, data="{", content_type="application/json")
        self.assertEqual(malformed.status_code, 400)
        invalid_email = self.client.patch(
            url,
            data=json.dumps({"email": "bad-email"}),
            content_type="application/json",
        )
        self.assertEqual(invalid_email.status_code, 400)
        duplicate_email = self.client.patch(
            url,
            data=json.dumps({"email": self.second_profile.email}),
            content_type="application/json",
        )
        self.assertEqual(duplicate_email.status_code, 409)
        duplicate_name = self.client.patch(
            url,
            data=json.dumps({"name": self.second_profile.username}),
            content_type="application/json",
        )
        self.assertEqual(duplicate_name.status_code, 409)
        unknown_field = self.client.patch(
            url,
            data=json.dumps({"password": "never"}),
            content_type="application/json",
        )
        self.assertEqual(unknown_field.status_code, 400)

    def test_update_and_delete_missing_users_return_not_found(self):
        update = self.client.patch(
            reverse("api-user-update", args=["missing@example.test"]),
            data=json.dumps({"name": "Missing"}),
            content_type="application/json",
        )
        self.assertEqual(update.status_code, 404)
        delete = self.client.delete(
            reverse("api-user-delete", args=["missing@example.test"])
        )
        self.assertEqual(delete.status_code, 404)

    def test_delete_removes_profile_and_linked_auth_user(self):
        response = self.client.delete(
            reverse("api-user-delete", args=[self.first_profile.email])
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(UserDetails.objects.filter(pk="First User").exists())
        self.assertFalse(User.objects.filter(pk=self.first_user.pk).exists())

    def test_unsupported_method_returns_json_405(self):
        response = self.client.post(reverse("api-users"), data={})
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json()["allowed_methods"], ["GET"])

    def test_api_mutation_requires_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.staff)
        response = csrf_client.delete(
            reverse("api-user-delete", args=[self.first_profile.email])
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"].startswith("CSRF verification failed"), True)
