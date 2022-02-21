from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from ..models import Post, Group

User = get_user_model()


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth',)
        cls.not_auth = User.objects.create_user(username='not_author',)
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug='testslug',
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            text="Тестовая группа",
            author=cls.user,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_second = Client()
        self.authorized_client_second.force_login(self.not_auth)

# Проверяем общедоступные страницы

    def test_url_all(self):
        """Доступность URL для незарегистрированных пользователей"""
        url_list = [
            '/',
            f'/group/{self.group.slug}/',
            '/profile/auth/',
            f'/posts/{self.post.id}/',
        ]
        for url in url_list:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    200
                )

    def test_url_unexisting_page(self):
        """Проверка ответа несуществующей страницы"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)

    # Доступность страниц для авторизованного пользователя

    def test_url_post_create(self):
        """Проверка доступа для авторизованного пользователя"""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)

    # Редиректы для неавторизованного пользователя

    def test_url_post_create_redirect(self):
        """Проверка перенаправления на страницу логина"""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    # Страница редактирования поста доступна автору
    # для авторизованного пользователя не автора редирект на страницу поста

    def test_post_edit_author(self):
        """Проверка соответстия шаблона редактирования для автора поста"""
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/'
        )
        template = 'posts/create_post.html'
        self.assertTemplateUsed(response, template)

    def test_post_edit_not_author(self):
        """Проверка редиректа для не автора поста"""
        response = self.authorized_client_second.get(
            f'/posts/{self.post.id}/edit/'
        )
        self.assertRedirects(
            response, f'/posts/{self.post.id}/'
        )

    def test_comment_create_guest_user(self):
        '''неавторизованный пользователь перенаправляется на страницу логина'''
        response = self.guest_client.get(
            f'/posts/{self.post.id}/comment/'
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.pk}/comment/'
        )

    # Проверка вызываемых шаблонов для каждого адреса

    def test_correct_template(self):
        """Проверка соответствия шаблонов url"""
        url_template_dict = {
            '/': 'posts/index.html',
            '/group/testslug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in url_template_dict.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
