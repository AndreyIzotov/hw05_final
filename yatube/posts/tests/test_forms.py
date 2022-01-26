import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from posts.models import Post, Group, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTesting(TestCase):
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = PostCreateFormTesting.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст новый',
            'group': self.group.id,
            'image': image,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:profile',
                              kwargs={'username': self.user.username})
        )
        first_post = Post.objects.first()
        list_post_image = list(str(first_post.image))
        list_post_image[11:19] = []
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(first_post.text, form_data['text'])
        self.assertEqual(first_post.group.id, form_data['group'])
        self.assertEqual(first_post.author, self.user)
        self.assertEqual(
            ''.join(list_post_image) + '.gif', f'posts/{form_data["image"]}'
        )

    def test_edit_post(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст новый',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        edited_post = Post.objects.first()
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(
            response, reverse('posts:post_detail',
                              kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(edited_post.text, form_data['text'])
        self.assertEqual(edited_post.group.id, form_data['group'])
        self.assertEqual(edited_post.author, self.user)

    def test_not_authorized_client_create_post(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст новый',
            'group': self.group.id
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('users:login')
            + '?next=' + reverse('posts:post_create')
        )
        self.assertEqual(Post.objects.count(), post_count)

    def test_not_authorized_client_comment(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Текст комментария',
        }
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)

    def test_add_comment(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Текст комментария',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)

    def test_cache(self):
        cache.delete('index_page')
        new_post = Post.objects.create(
            author=PostCreateFormTesting.user,
            text='Тестовый текст новый',
            group=PostCreateFormTesting.group,
        )
        response = self.guest_client.get(reverse('posts:index'))
        self.assertTrue(
            new_post.text in response.context['page_obj'][0].text)
        new_post_2 = Post.objects.create(
            author=PostCreateFormTesting.user,
            text='Тестовый текст новый 1',
            group=PostCreateFormTesting.group,
        )
        self.assertFalse(
            new_post_2.text in response.context['page_obj'][0].text)
        cache.delete('index_page')
