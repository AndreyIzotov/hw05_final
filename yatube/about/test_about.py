from django.test import TestCase, Client


class StaticURLTests(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_about_page(self):
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, 200)

    def test_tech_page(self):
        response = self.guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            '/about/author/': 'about/author.html/',
            '/about/tech/': 'about/tech.html/'
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
