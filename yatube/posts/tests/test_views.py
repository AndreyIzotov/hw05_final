import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django import forms

from posts.models import Post, Group, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


def _test_context(self, test_object):
    index_text = test_object.text
    index_author = test_object.author.username
    index_group = test_object.group.title
    self.assertEqual(index_text, self.post.text)
    self.assertEqual(index_author, self.user.username)
    self.assertEqual(index_group, self.group.title)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(
            username='NoName',
            email='1@1.com',
            password='Ss12345678')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовая группа'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=cls.image,
        )
        cls.group_new = Group.objects.create(
            title='Тестовая группа новая',
            slug='test_slug_new',
            description='Тестовая группа новая'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = StaticURLTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}): (
                'posts/group_list.html'
            ),
            (reverse('posts:profile',
                     kwargs={'username': self.user.username})): (
                'posts/profile.html'
            ),
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}): (
                'posts/post_detail.html'
            ),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}): (
                'posts/create_post.html'
            ),
            reverse('posts:post_create'): 'posts/create_post.html'
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_corect_context(self):
        response = self.client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        _test_context(self, first_object)

    def test_group_list_page_show_corect_context(self):
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        first_object = response.context['page_obj'][0]
        _test_context(self, first_object)

    def test_profile_page_show_corect_context(self):
        response = self.client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        first_object = response.context['page_obj'][0]
        _test_context(self, first_object)

    def test_post_detail_page_show_corect_context(self):
        response = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        post_context = response.context.get('post')
        self.assertEqual(
            post_context.author.username, self.user.username)
        self.assertEqual(
            post_context.text, self.post.text)
        self.assertEqual(
            post_context.group.title, self.group.title)

    def test_post_edit_page_show_corect_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_create_page_show_corect_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def post_in_pages(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(response.context['page_obj'][0], self.post)
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context['page_obj'][0], self.post)
        response = self.client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(response.context['page_obj'][0], self.post)

    def test_new_group_post(self):
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(
            len(response.context['page_obj']),
            self.group.posts.count()
        )
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': self.group_new.slug})
        )
        self.assertEqual(len(response.context['page_obj']), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(
            username='NoName',
            email='1@1.com',
            password='Ss12345678')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовая группа'
        )
        cls.posts_count = 13
        cls.objs = [Post(author=cls.user,
                         text='Тестовый текст',
                         group=cls.group)
                    for i in range(0, cls.posts_count)]
        Post.objects.bulk_create(cls.objs, cls.posts_count)
        cls.last_part_posts = Post.objects.count() % settings.POSTS_ON_PAGES

    def setUp(self):
        self.guest_client = Client()
        self.user = PaginatorViewsTest.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(
            len(response.context['page_obj']), settings.POSTS_ON_PAGES)

    def test_second_page_contains_three_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']), self.last_part_posts)

    def test_first_page_group_list_contains_ten_records(self):
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(
            len(response.context['page_obj']), settings.POSTS_ON_PAGES)

    def test_second_page_group_list_contains_ten_records(self):
        response = self.client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}) + '?page=2'
        )
        self.assertEqual(
            len(response.context['page_obj']), self.last_part_posts)

    def test_first_page_profile_contains_ten_records(self):
        response = self.client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(
            len(response.context['page_obj']), settings.POSTS_ON_PAGES)

    def test_second_page_profile_contains_ten_records(self):
        response = self.client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user.username}) + '?page=2'
        )
        self.assertEqual(
            len(response.context['page_obj']), self.last_part_posts)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(
            username='NoName',
            email='1@1.com',
            password='Ss12345678')
        cls.author = User.objects.create_user(
            username='Author',
            email='2@2.com',
            password='Ss1234567890'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
            group=cls.group,
            image=cls.image,
        )

    def setUp(self):
        self.user = Client()
        self.user.force_login(FollowTest.user)
        self.author = Client()
        self.author.force_login(FollowTest.author)

    def test_user_can_follow(self):
        self.user.get(reverse('profile_follow', kwargs={
            'username': self.author.username,
        }))
        self.assertEqual(Follow.objects.count(), 1)

    def test_user_can_unfollow(self):
        self.user.get(reverse('profile_unfollow', kwargs={
            'username': self.author.username,
        }))
        self.assertEqual(Follow.objects.count(), 0)