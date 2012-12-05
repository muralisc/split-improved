"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from projectApp1.models import Membership, Group
from TransactionApp.models import Category, UserCategory, GroupCategory


class TransactionAppTestCase(TestCase):

    def setUp(self):
        '''
        default user
        default group
        '''
        u1 = User.objects.create_user(username="jayalalv@default.com", email="jayalalv@default.com", password="solar")
        u2 = User.objects.create_user(username="gman@default.com", email="gman@default.com", password="p")
        u3 = User.objects.create_user(username="swathi@default.com", email="swathi@default.com", password="p")
        u4 = User.objects.create_user(username="anakha@default.com", email="anakha@default.com", password="p")
        u5 = User.objects.create_user(username="daddy@default.com", email="kurian@default.com", password="p")

        g1 = Group.objects.create(name='car', description='just for the sake of testing', privacy=0, deleted=False)

        Membership.objects.create(group=g1, user=u1, administrator=True, positions='creator', amount_in_pool=0)
        Membership.objects.create(group=g1, user=u2, administrator=False, positions='', amount_in_pool=0)
        Membership.objects.create(group=g1, user=u3, administrator=False, positions='', amount_in_pool=0)
        Membership.objects.create(group=g1, user=u4, administrator=False, positions='', amount_in_pool=0)
        Membership.objects.create(group=g1, user=u5, administrator=False, positions='', amount_in_pool=0)
        pass

    def test_create_category(self):
        """
        no category of duplicate name is posrrble
        wrong credentials issue
        gid creates a group category
        otherwisea a user category is created
        """
        #login
        self.client.login(username="jayalalv@default.com", password="solar")
        # create a category as user
        self.assertFalse(Category.objects.filter(name='SBI').exists())
        u1 = User.objects.get(username="jayalalv@default.com")
        response = self.client.get('/createCategory/0/', {'name': 'SBI', 'category_type': 1, 'description': '', 'privacy': '0', 'created_by': u1.pk})
        # verify created userCategory and Category
        self.assertTrue(Category.objects.filter(name='SBI').exists())
        self.assertEqual(1, UserCategory.objects.all().count())
        self.assertEqual(0, GroupCategory.objects.all().count())
        # create a category as group of same name
        g1 = Group.objects.get(name='car')
        response = self.client.get(
                                    '/createCategory/{0}/'.format(g1.pk),
                                    {
                                        'name': 'SBI',
                                        'category_type': 1,
                                        'description': '',
                                        'privacy': 0,
                                        'created_by': u1.pk
                                    }
                                   )
        # verify only GroupCategory is created
        self.assertTrue(1, Category.objects.filter(name='SBI').count())
        self.assertEqual(1, UserCategory.objects.all().count())
        self.assertEqual(1, GroupCategory.objects.all().count())
        # if a Usercategory exist do not create again
        # if a Groupcategory exist do not create again

    def test_displayTransactionForm(self):
        #login using url to update the session variable
        response = self.client.post('/login/', {'email': 'jayalalv@default.com', 'password': 'solar'}, follow=True)
        response = self.client.post('/transactionForm/', follow=True)
        self.assertEqual(response.status_code, 200)
        pass
