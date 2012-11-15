"""
from django.test.utils import setup_test_environment
setup_test_environment()
from django.test.client import Client
c = Client()
response = c.post('/login/', {'username': 'john', 'password': 'smith'})
response.status_code
"""

from django.test import TestCase
from django.contrib.auth.models import User


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests createUser() and siteLogin()
        A regular call to /createUser/ redirects to /login/
        create user should not create for invalid email
        Create a user,
        accessing the /login/ page after usr login will fetch /login/
        login into the created user(check weather the user is actually created),
        accessing the /login/ page after usr login will fetch /home/
        logout
        login with wrong password
        """
        response = self.client.post('/createUser/', follow=True)
        self.assertEqual(response.request['PATH_INFO'], '/login/')
        response = self.client.post('/createUser/', {'email': 'jayalalvgmail.com', 'password': 'solar'}, follow=True)
        self.assertEqual(response.context['form'].is_valid(), False)
        response = self.client.post('/createUser/', {'email': 'jayalalv@gmail.com', 'password': 'solar'}, follow=True)
        self.assertEqual(response.request['PATH_INFO'], '/login/')
        response = self.client.post('/login/', follow=True)
        self.assertEqual(response.request['PATH_INFO'], '/login/')
        response = self.client.post('/login/', {'email': 'jayalalv@gmail.com', 'password': 'solar'}, follow=True)
        self.assertEqual(response.request['PATH_INFO'], '/home/')
        response = self.client.post('/login/', follow=True)
        self.assertEqual(response.request['PATH_INFO'], '/home/')
        response = self.client.logout()
        response = self.client.post('/login/', {'email': 'jayalalv@gmail.com', 'password': 'wrongpassword'}, follow=True)
        self.assertEqual(response.request['PATH_INFO'], '/login/')
