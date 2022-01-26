from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(
            username='NoName',
            email='1@1.com',
            password='Ss12345678')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='1',
            description='Тестовая группа'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = StaticURLTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_status_code(self):
        pages = {
            'index': reverse('posts:index'),
            'group': (reverse('posts:group_list',
                      kwargs={'slug': self.group.slug})),
            'profile': (reverse('posts:profile',
                        kwargs={'username': self.user.username})),
            'post_detail': (reverse('posts:post_detail',
                            kwargs={'post_id': self.post.id})),
            'create': reverse('posts:post_create'),
            'post_edit': (reverse('posts:post_edit',
                          kwargs={'post_id': self.post.id}))
        }
        for name, reverse_name in pages.items():
            with self.subTest(name=name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.status_code, 200)

    def test_unexisting_page(self):
        response = self.guest_client.get('/unexisting/')
        self.assertEqual(response.status_code, 404)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
