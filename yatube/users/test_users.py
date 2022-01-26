from django.contrib.auth import get_user_model
from django.test import TestCase, Client

User = get_user_model()


class StaticURLTests(TestCase):

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='NoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_login_page(self):
        response = self.guest_client.get('/auth/login/')
        self.assertEqual(response.status_code, 200)

    def test_signup_page(self):
        response = self.guest_client.get('/auth/signup/')
        self.assertEqual(response.status_code, 200)

    def test_logout_page(self):
        response = self.authorized_client.get('/auth/logout/')
        self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            '/auth/login/': 'registration/login.html',
            '/auth/signup/': 'users/signup.html',
            '/auth/logout/': 'users/logged_out.html'
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
