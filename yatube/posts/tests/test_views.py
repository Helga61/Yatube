import datetime
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Post, Group, Follow
from posts.forms import PostForm
from posts.conf import NUMBER_OF_POSTED

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth',)
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug='testslug',
            description="Тестовое описание",
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.posts = [
            Post(
                author=cls.user,
                text=f'Текст поста №{index}',
                group=cls.group,
                image=uploaded,
                pk=index) for index in range(1, 14)
        ]
        Post.objects.bulk_create(cls.posts)
        for index in range(13):
            minute = datetime.timedelta(minutes=index)
            cls.posts[index].pub_date += minute
        Post.objects.bulk_update(cls.posts, ['pub_date'])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.get(pk=13)

# проверка namespace:name

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': 'testslug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': 'auth'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.pk}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.pk}
            ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

# Проверяем контекст и паджинатор

    def test_index_correct_context(self):
        """Проверка контекста и паджинатора главной страницы"""
        response = self.authorized_client.get(reverse('posts:index'))
        response_second_page = self.client.get(reverse(
            'posts:index') + '?page=2'
        )
        first_object = response.context['page_obj'][0]
        context_dict = {
            first_object.text: f'Текст поста №{self.post.pk}',
            first_object.pub_date: self.post.pub_date,
            first_object.author.username: 'auth',
            first_object.image: self.post.image
        }
        for object, context in context_dict.items():
            with self.subTest(object=object):
                self.assertEqual(object, context)
        self.assertEqual(len(response.context['page_obj']), NUMBER_OF_POSTED)
        self.assertEqual(len(response_second_page.context['page_obj']), 3)

    def test_group_list_correct_context(self):
        """Проверка контекста и паджинатора страницы группы"""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'testslug'})
        )
        response_second_page = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': 'testslug'}) + '?page=2'
        )
        test_object = response.context['page_obj'][0]
        group_object = response.context['group']
        context_dict = {
            test_object.text: f'Текст поста №{self.post.pk}',
            test_object.pub_date: self.post.pub_date,
            test_object.author.username: 'auth',
            test_object.image: self.post.image,
            group_object.title: 'Тестовая группа',
            group_object.slug: 'testslug',
            group_object.description: 'Тестовое описание',
        }
        for object, context in context_dict.items():
            with self.subTest(object=object):
                self.assertEqual(object, context)
        self.assertEqual(len(response.context['page_obj']), NUMBER_OF_POSTED)
        self.assertEqual(len(response_second_page.context['page_obj']), 3)

    def test_profile_context(self):
        """Проверка контекста и паджинатора страницы автора"""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': 'auth'})
        )
        response_second_page = self.client.get(reverse(
            'posts:profile', kwargs={'username': 'auth'}) + '?page=2'
        )
        author_object = response.context['author']
        text_object = response.context['page_obj'][0]
        count_posts_object = response.context['count_of_posts']
        context_dict = {
            author_object: self.post.author,
            text_object.text: f'Текст поста №{self.post.pk}',
            text_object.pub_date: self.post.pub_date,
            text_object.image: self.post.image,
            count_posts_object: 13
        }
        for object, context in context_dict.items():
            with self.subTest(object=object):
                self.assertEqual(object, context)
        self.assertEqual(len(response.context['page_obj']), NUMBER_OF_POSTED)
        self.assertEqual(len(response_second_page.context['page_obj']), 3)

    def test_post_detail_context(self):
        """Проверка контекста страницы поста"""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        text_object = response.context['post']
        author_object = response.context['author']
        count_posts_object = response.context['count_of_posts']
        group_object = response.context['group']
        context_dict = {
            author_object: self.post.author,
            text_object.text: f'Текст поста №{self.post.pk}',
            text_object.pub_date: self.post.pub_date,
            text_object.image: self.post.image,
            count_posts_object: 13,
            group_object.title: 'Тестовая группа'
        }
        for object, context in context_dict.items():
            with self.subTest(object=object):
                self.assertEqual(object, context)

    def test_post_create_context(self):
        """Проверка полей форм страницы создания поста"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_context(self):
        """Проверка полей форм страницы редактирования поста"""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(
                    value
                )
                self.assertIsInstance(form_field, expected)


class PostCreateTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Новый автор')
        cls.form = PostForm()
        cls.group = Group.objects.create(
            title="Новая группа",
            slug='test-slug',
            description="Новое описание",
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create(self):
        """проверяем, что при создании нового поста он появляется на главной странице,
        странице группы и в профайле"""
        new_post = Post.objects.create(
            author=self.user,
            text='New post',
            group=self.group
        )
        reverse_list = [
            reverse('posts:index'),
            reverse(
                'posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse(
                'posts:profile', kwargs={'username': 'Новый автор'})
        ]
        for inverse in reverse_list:
            with self.subTest(inverse=inverse):
                response = self.authorized_client.get(inverse)
                text_object = response.context['page_obj'][0]
                self.assertEqual(new_post, text_object)

    def test_post_no_group_create(self):
        """Проверяем, что пост без группы не попадает в записи группы"""
        Post.objects.create(
            author=self.user,
            text='New post2',
        )
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test-slug'}))
        post_count = len(response.context['page_obj'])
        self.assertEqual(post_count, 0)

    def test_cache_page_idex(self):
        '''Новый пост остается в кэше до очистки'''
        cache.clear()
        post = Post.objects.create(
            author=self.user,
            text='Проверка кэша',
        )
        response = self.authorized_client.get(reverse('posts:index'))
        cache_after_adding = response.content
        post.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        cache_after_del = response.content
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(cache_after_adding, cache_after_del)
        self.assertNotEqual(cache_after_del, response.content)


class PostFollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Подписчик')
        cls.user_auth = User.objects.create_user(username='Авор')
        cls.post = Post.objects.create(
            author=cls.user_auth,
            text='New post'
        )
        Follow.objects.create(
            user=cls.user,
            author=cls.user_auth
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_follow_authorized_user(self):
        """Авторизованный пользователь может подписываться на других"""
        """новая запись появляется в ленте подписчика"""
        response = self.authorized_client.get(reverse(
            'posts:follow_index'
        ))
        follow_posts = len(response.context['page_obj'])
        self.assertEqual(follow_posts, 1)
        post = Post.objects.get(id=self.post.pk)
        self.assertIn(post, response.context['page_obj'])

    def test_unfollow_autorized_user(self):
        """Авторизованный пользователь может отписаться от автора"""
        """новая запись не появится в его ленте подписок"""
        Follow.objects.get(
            user=self.user,
            author=self.user_auth
        ).delete()
        response = self.authorized_client.get(reverse(
            'posts:follow_index'
        ))
        follow_posts = len(response.context['page_obj'])
        self.assertEqual(follow_posts, 0)
        post = Post.objects.get(id=self.post.pk)
        self.assertNotIn(post, response.context['page_obj'])
