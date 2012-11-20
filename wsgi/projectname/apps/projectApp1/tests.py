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
from projectApp1.models import Membership, Group


class UserManagementTestCase(TestCase):

    def setUp(self):
        # This function is automatically called in the beginig
        User.objects.create_user(username="default@default.com", email="default@default.com", password="default")
        User.objects.create_user(username="default1@default.com", email="default1@default.com", password="default1")

    def test_createUser_siteLogin(self):
        """
        Tests createUser() and siteLogin()
        A regular call to /createUser/ redirects to /login/
        create user should not create for invalid email
        Create a user,
        accessing the /login/ page after user login will fetch /login/
        login into the created user(check weather the user is actually created),
        accessing the /login/ page after user login will fetch /home/
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
        self.assertTrue(response.context['wrongUsernameOrPassword'])

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
        self.client.login(username="default@default.com", password='default')
        # invalid codename
        response = self.client.post('/permission/invalid_codename/dissable/', follow=True)
        self.assertEqual(response.request['PATH_INFO'], '/settings/')
        # invalid enable|dissble
        response = self.client.post('/permission/personal_transactions/diable/', follow=True)
        self.assertEqual(response.status_code, 404)
        # add a permission and remove a permision
        response = self.client.post('/permission/personal_transactions/enable/', follow=True)
        self.assertTrue(response.context['user'].has_perm('TransactionApp.personal_transactions'))
        response = self.client.post('/permission/personal_transactions/dissable/', follow=True)
        self.assertFalse(response.context['user'].has_perm('TransactionApp.personal_transactions'))

    def test_settings(self):
        pass

    def test_groupHome(self):
        '''
        Tests groupHome() and createGroup()
        createGroup()
            a valid entry should create an entry in model
            an invalid user id in members form will nvalidate the form
            creating user should be an administrator
        createHome()
            invalid id in url
            valid id and url
        '''
        self.client.login(username='default@default.com', password='default')
        # invalid group if rediredts to 404
        response = self.client.post('/group/0/')
        self.assertEqual(response.status_code, 404)
        # crete a group and verify admin is the logged in user
        response = self.client.post('/createGroup/',
                                    {'name': 'group1', 'description': 'group1_desc', 'members': [User.objects.get(username='default1@default.com').id]},
                                    follow=True)
        self.assertEqual(Membership.objects.get(administrator=True).user.username, 'default@default.com')
        # valid groupid in url
        group = Group.objects.get(name='group1')
        response = self.client.post('/group/{0}/'.format(group.id))
        self.assertEqual(response.context['group'], group)
