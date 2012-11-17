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


class UserManagementTestCase(TestCase):

    def setUpa(self):
        # self.defaultUser =
        User.objects.create_user(username="default@default.com", email="default@default.com", password="default")

    def test_createUser_siteLogin(self):
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

    def test_permissions(self):
        '''
        testing view enableDissablePermissions
        after logging in
            cant remove from an empty permissions set[handled by djnago]
            add exixting permission againt[handled by djnago]
        '''
        # withot logging in user cant change permissions, redirected to login page
        response = self.client.post('/permission/personal_transactions/dissable/', follow=True)
        self.assertEqual(response.request['PATH_INFO'], '/login/')
        # setup the deafult user
        self.setUpa()
        self.client.login(username="default@default.com", password='default')
        # invalid codename
        response = self.client.post('/permission/invalid_codename/dissable/', follow=True)
        self.assertEqual(response.request['PATH_INFO'], '/settings/')
        # invalid enable|dissble
        response = self.client.post('/permission/personal_transactions/diable/', follow=True)
        self.assertEqual(response.status_code, 404)
        # add a permission and remove a permision
        response = self.client.post('/permission/personal_transactions/enable/', follow=True)
        self.assertTrue(response.context['user'].has_perm('projectApp1.personal_transactions'))
        response = self.client.post('/permission/personal_transactions/dissable/', follow=True)
        self.assertFalse(response.context['user'].has_perm('projectApp1.personal_transactions'))
