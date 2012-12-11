from django.test import TestCase
from django.contrib.auth.models import User
from projectApp1.models import Membership, Group, Invite
from django.test.client import RequestFactory


class UserManagementTestCase(TestCase):

    def setUp(self):
        # This function is automatically called in the beginig
        # setup 3 default users
        self.factory = RequestFactory()
        self.u = User.objects.create_user(username="default@default.com", email="default@default.com", password="default")
        self.u1 = User.objects.create_user(username="default1@default.com", email="default1@default.com", password="default1")
        self.u2 = User.objects.create_user(username="default2@default.com", email="default2@default.com", password="default2")
        self.u3 = User.objects.create_user(username="jayalalv@default.com", email="jayalalv@default.com", password="solar")
        # setup a default group

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

    def test_createGroup(self):
        '''
        Tests groupHome() and createGroup()
        createGroup()
            a valid entry should create an entry in model
            an invalid user id in members form will invalidate the form
            creating user will be an administrator
            check it creates one Membership and remaining Invite objects
        createHome()
            invalid id in url
            valid id and url
        '''
        self.client.login(username='default@default.com', password='default')
        # crete a group and verify admin is the logged in user
        response = self.client.post('/createGroup/',
                                    {
                                    'name': 'group1',
                                    'description': 'group1_desc',
                                    'privacy': '0',
                                    'members': '{0},{1}'.format(
                                    self.u1.id, # User.objects.get(username='default1@default.com').id,
                                    self.u2.id, # User.objects.get(username='default2@default.com').id,
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
        # url to a deleted group raises http404
        group.deleted = True
        group.save()
        response = self.client.post('/group/{0}/'.format(group.id))
        self.assertEqual(response.status_code, 404)
        # the check box should sent only valid group members

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
                                    {
                                    'name': 'group1',
                                    'description': 'group1_desc',
                                    'privacy': '0',
                                    'members': '{0},{1}'.format(
                                    self.u1.id,
                                    self.u2.id,
                                    )},
                                    follow=True)
        # a invalid user tries to change invite of another user
        invite_of_default1 = Invite.objects.get(to_user=self.u1)                        # User.objects.get(username='default1@default.com'))
        response = self.client.post('/invite/accept/{0}/'.format(invite_of_default1.id))
        self.assertEqual(response.status_code, 404)
        # a valid user tries to delete invite invite deleted
        response = self.client.logout()
        self.client.login(username='default1@default.com', password='default1')
        # chumma request = self.factory.get('/home/')
        response = self.client.post('/invite/decline/{0}/'.format(invite_of_default1.id))
        self.assertEqual(Invite.objects.filter(to_user=self.u1).count(), 0)
        # a valid user tries to accept the invite a membership row is created
        response = self.client.logout()
        self.client.login(username='default2@default.com', password='default2')
        invite_of_default2 = Invite.objects.get(to_user=self.u2)
        no_of_membership = Membership.objects.all().count()
        response = self.client.post('/invite/accept/{0}/'.format(invite_of_default2.id))
        self.assertEqual(Membership.objects.all().count(), no_of_membership + 1)
        # manually create an invite for a membership that already exist and then
        # try to change[accept] it to a membership using /changeInvite/ [should fail]
        temp_invite = Invite.objects.create(
                                        from_user=self.u1,                              # User.objects.get(username='default1@default.com'),
                                        to_user=self.u2,                                # User.objects.get(username='default2@default.com'),
                                        group=Group.objects.get(name='group1'),
                                        unread=True,
                                        message=''
                                        )
        no_of_membership = Membership.objects.all().count()
        response = self.client.post('/invite/accept/{0}/'.format(temp_invite.id))
        self.assertEqual(Membership.objects.all().count(), no_of_membership)

    def test_getJSON_users(self):
        '''
        invalid query / no query
        valid query with incomlete dictionary keys in GET
        valid query with complete GET dictionary
        '''
        pass

    def test_deleteGroup(self):
        '''
        non admin user cant delete
        admin user can delete
        actual record is not deleted only a field changes
        invalid group id in url
        '''
        self.client.login(username='default@default.com', password='default')
        group = Group.objects.create(
                                    name='default_group',
                                    description='default description',
                                    privacy=0,
                                    deleted=False
                                    )
        Membership.objects.create(
                                group=group,
                                user=User.objects.get(username='default1@default.com'),
                                administrator=True,
                                positions='creator',
                                amount_in_pool=0
                                )
        Membership.objects.create(
                                group=group,
                                user=User.objects.get(username='default2@default.com'),
                                administrator=False,
                                positions='',
                                amount_in_pool=0
                                )
        # non admin user cant delete
        response = self.client.post('/deleteGroup/{0}/'.format(group.pk))
        self.assertFalse(Group.objects.get(name='default_group').deleted)
        # admin user can delete
        self.client.logout()
        self.client.login(username='default1@default.com', password='default1')
        response = self.client.post('/deleteGroup/{0}/'.format(group.pk))
        self.assertTrue(Group.objects.get(name='default_group').deleted)
        # invalid group id in url
        response = self.client.post('/deleteGroup/0/')
        self.assertEqual(response.status_code, 404)

    def test_Group_invite(self):
        '''
        this test the member funtion of Groups model
        invite(self, sender, recievers, msg='')
            try to create a invite for a membership that alredy exist
            try to create a invite for an invite that alredy exist
        '''
        # create a group and try to create an invite for the exiting membership
        # assert that no new invite is created
        self.client.login(username='default@default.com', password='default')
        response = self.client.post('/createGroup/',
                                    {
                                        'name': 'group1',
                                        'description': 'group1_desc',
                                        'privacy': '0',
                                        'members': '{0},{1}'.format(
                                        User.objects.get(username='default1@default.com').id,
                                        User.objects.get(username='default2@default.com').id,
                                        )},
                                    follow=True)
        # INFO one membership and 2 invites exist now
        self.client.logout()
        self.client.login(username='default1@default.com', password='default1')
        group = Group.objects.get(name='group1')
        no_of_invites = Invite.objects.all().count()
        group.invite(response.context['user'], [User.objects.get(username='default@default.com')])
        self.assertEqual(Invite.objects.all().count(), no_of_invites)
        # try to invite an existing invite
        group.invite(response.context['user'], [User.objects.get(username='default1@default.com')])
        self.assertEqual(Invite.objects.all().count(), no_of_invites)

    def test_sentInvite(self):
        '''
        only members of a group can sent invite\else http404
        '''
        # login user and create a group
        self.client.login(username='default@default.com', password='default')
        response = self.client.post('/createGroup/',
                                    {
                                        'name': 'group1',
                                        'description': 'group1_desc',
                                        'privacy': '0',
                                        'members': '{0}'.format(
                                        User.objects.get(username='default1@default.com').id,
                                        )},
                                    follow=True)
        group = Group.objects.get(name='group1')
        self.assertEqual(1, Invite.objects.filter(group=Group.objects.get(name='group1')).count())
        # a invalid user tries to invite
        response = self.client.logout()
        self.client.login(username='jayalalv@default.com', password='solar')
        response = self.client.post(
                                    '/sentInvites/{0}/'.format(group.id),
                                    {'members': '{0}'.format(
                                                                User.objects.get(username='default2@default.com').id,
                                                                )},
                                    )
        self.assertEqual(response.status_code, 404)
        # a valid user tries to invite
        self.client.login(username='default@default.com', password='default')
        response = self.client.post(
                                    '/sentInvites/{0}/'.format(group.id),
                                    {'members': '{0},{1}'.format(
                                                                User.objects.get(username='default1@default.com').id,
                                                                User.objects.get(username='default2@default.com').id,
                                                                )},
                                    )
        self.assertEqual(2, Invite.objects.filter(group=Group.objects.get(name='group1')).count())

    def test_changeGroup(self):
        '''
        check if gid is valid
        the user is a member
        check in get query redirects properly
        '''
        # login user and create a group
        self.client.login(username='default@default.com', password='default')
        response = self.client.post('/createGroup/',
                                    {
                                    'name': 'group1',
                                    'description': 'group1_desc',
                                    'privacy': '0',
                                    'members': '{0}'.format(
                                    User.objects.get(username='default1@default.com').id,
                                    )},
                                    )
        response = self.client.post('/createGroup/',
                                    {
                                        'name': 'group2',
                                        'description': 'group2_desc',
                                        'privacy': '0',
                                        'members': '{0}'.format(
                                        User.objects.get(username='default1@default.com').id,
                                        )},
                                    )
        # invalid gid
        response = self.client.get('/changeGroup/100/')
        self.assertEqual(response.status_code, 404)
        # invalid logged in user
        group = Group.objects.get(name='group1')
        response = self.client.logout()
        self.client.login(username='jayalalv@default.com', password='solar')
        response = self.client.get('/changeGroup/{0}/'.format(group.id))
        self.assertEqual(response.status_code, 404)
        # valid user
        response = self.client.logout()
        self.client.login(username='default@default.com', password='default')
        self.assertFalse('active_group' in self.client.session)
        response = self.client.get('/changeGroup/{0}/'.format(group.id))
        self.assertTrue('active_group' in self.client.session)
