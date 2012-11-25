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
from projectApp1.models import Membership, Group, Invite
from django.test.client import RequestFactory


class UserManagementTestCase(TestCase):

    def setUp(self):
        # This function is automatically called in the beginig
        self.factory = RequestFactory()
        User.objects.create_user(username="default@default.com", email="default@default.com", password="default")
        User.objects.create_user(username="default1@default.com", email="default1@default.com", password="default1")
        User.objects.create_user(username="default2@default.com", email="default2@default.com", password="default2")

    def test_createUser_siteLogin(self):
        """
        Tests createUser() and siteLogin()
        A non POST call to /createUser/ redirects to /login/
        create user should not create for invalid email
        Create a user,
        accessing the /login/ page after user login will fetch /login/
        login into the created user(check weather the user is actually created),
        accessing the /login/ page after user login will fetch /home/
        logout
        login with wrong password
        """
        response = self.client.post('/createUser/', follow=True)
        self.assertEqual(response.request['PATH_INFO'], '/createUser/')
        response = self.client.post('/createUser/', {'email': 'jayalalvgmail.com', 'password': 'solar'}, follow=True)
        self.assertEqual(response.context['form'].is_valid(), False)
        response = self.client.post('/createUser/', {'email': 'jayalalv@gmail.com', 'password': 'solar'}, follow=True)
        self.assertEqual(response.request['PATH_INFO'], '/createUser/')
        response = self.client.post('/login/', follow=True)
        self.assertEqual(response.request['PATH_INFO'], '/login/')
        response = self.client.post('/login/', {'email': 'jayalalv@gmail.com', 'password': 'solar'}, follow=True)
        self.assertEqual(response.request['PATH_INFO'], '/home/')
        response = self.client.post('/login/', follow=True)
        self.assertEqual(response.request['PATH_INFO'], '/home/')
        response = self.client.logout()
        response = self.client.post('/login/', {'email': 'jayalalv@gmail.com', 'password': 'wrongpassword'}, follow=True)
        self.assertTrue(response.context['wrongUsernameOrPassword'])
        #logout and check of an arbitary url after login site redirects to arbitary url

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

    def test_Group(self):
        '''
        Tests groupHome() and createGroup()
        createGroup()
            a valid entry should create an entry in model
            an invalid user id in members form will invalidate the form
            creating user will be an administrator
            check it creates one member and remaining invite objects
        createHome()
            invalid id in url
            valid id and url
        '''
        self.client.login(username='default@default.com', password='default')

        # crete a group and verify admin is the logged in user
        response = self.client.post('/createGroup/',
                                    {'name': 'group1', 'description': 'group1_desc', 'members': '{0},{1}'.format(
                                        User.objects.get(username='default1@default.com').id,
                                        User.objects.get(username='default2@default.com').id,
                                        )},
                                    follow=True)
        self.assertEqual(Membership.objects.get(administrator=True).user.username, 'default@default.com')
        self.assertEqual(Membership.objects.get(positions='creator').user.username, 'default@default.com')
        # check it creates a group with only creator as the member
        self.assertEqual(1, Membership.objects.filter(group=Group.objects.get(name='group1')).count())
        # test the group has one and only one creator
        self.assertEqual(1, Membership.objects.filter(group=Group.objects.get(name='group1'), positions='creator').count())
        # check reaminig are invites
        self.assertEqual(2, Invite.objects.filter(group=Group.objects.get(name='group1')).count())

        # invalid group id rediredts to 404
        response = self.client.post('/group/0/')
        self.assertEqual(response.status_code, 404)
        # valid groupid in url
        group = Group.objects.get(name='group1')
        response = self.client.post('/group/{0}/'.format(group.id))
        self.assertEqual(response.context['group'], group)

    def test_changeInvite(self):
        '''
        only the user to whom the invite is for can change the invite
            any other user will get 404
        A valid url will:
            delete the invite
            accept: change the invite into membership
        '''
        # login user
        self.client.login(username='default@default.com', password='default')
        # create a group with some invites
        response = self.client.post('/createGroup/',
                                    {'name': 'group1', 'description': 'group1_desc', 'members': '{0},{1}'.format(
                                        User.objects.get(username='default1@default.com').id,
                                        User.objects.get(username='default2@default.com').id,
                                        )},
                                    follow=True)
        # a invalid user tries to change invite of another user
        invite_of_default1 = Invite.objects.get(to_user=User.objects.get(username='default1@default.com'))
        response = self.client.post('/invite/accept/{0}/'.format(invite_of_default1.id))
        self.assertEqual(response.status_code, 404)
        # a valid user tries to delete invite invite deleted
        response = self.client.logout()
        self.client.login(username='default1@default.com', password='default1')
        # chumma request = self.factory.get('/home/')
        response = self.client.post('/invite/decline/{0}/'.format(invite_of_default1.id))
        self.assertEqual(Invite.objects.filter(to_user=User.objects.get(username='default1@default.com')).count(), 0)
        # a valid user tries to accept the invite a membership row is created

    def test_getJSON_users(self):
        '''
        invalid query / no query
        valid query with incomlete dictionary keys in GET
        valid query with complete GET dictionary
        '''
        pass

    def test_deleteGroup(self):
        '''
        actual record is not deleted only a field changes
        non admin user cant delete
        admin user can delete
        '''
        pass
