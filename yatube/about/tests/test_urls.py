from http import HTTPStatus

from django.test import TestCase


class StaticURLTests(TestCase):

    def test_about(self):
        response = self.client.get('/about/author/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_tech(self):
        response = self.client.get('/about/tech/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
