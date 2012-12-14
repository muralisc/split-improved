from django.test import TestCase
from django.contrib.auth.models import User
from projectApp1.models import Membership, Group
from TransactionApp.models import Category, UserCategory, GroupCategory
from TransactionApp.__init__ import THIS_MONTH, LAST_MONTH, CUSTOM_RANGE, DEFAULT_START_PAGE, DEFAULT_RPP
from TransactionApp.helper import parseGET_initialise
from django.test.client import RequestFactory
from datetime import datetime


class TransactionAppTestCase(TestCase):

    def setUp(self):
        '''
        default user
        default group
        '''
        self.factory = RequestFactory()
        self.u1 = User.objects.create_user(username="jayalalv@default.com", email="jayalalv@default.com", password="solar")
        self.u2 = User.objects.create_user(username="ropo@default.com", email="ropo@default.com", password="p")
        self.u3 = User.objects.create_user(username="shakku@default.com", email="shakku@default.com", password="p")
        self.u5 = User.objects.create_user(username="daddy@default.com", email="kurian@default.com", password="p")
        self.u4 = User.objects.create_user(username="dash@default.com", email="dash@default.com", password="p")

        self.g1 = Group.objects.create(name='car', description='just for the sake of testing', privacy=0, deleted=False)

        Membership.objects.create(group=self.g1, user=self.u1, administrator=True, positions='creator', amount_in_pool=0)
        Membership.objects.create(group=self.g1, user=self.u2, administrator=False, positions='', amount_in_pool=0)
        Membership.objects.create(group=self.g1, user=self.u3, administrator=False, positions='', amount_in_pool=0)
        Membership.objects.create(group=self.g1, user=self.u4, administrator=False, positions='', amount_in_pool=0)
        Membership.objects.create(group=self.g1, user=self.u5, administrator=False, positions='', amount_in_pool=0)
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
        # if a Usercategory exist do not create again TODO
        # if a Groupcategory exist do not create again TODO

    def test_displayTransactionForm(self):
        #login using url to update the session variable
        response = self.client.post('/login/', {'email': 'jayalalv@default.com', 'password': 'solar'}, follow=True)
        response = self.client.post('/transactionForm/', follow=True)
        self.assertEqual(response.status_code, 200)
        pass

    def test_parseGET_initialise(self):
        '''
        sent valid values
        sent invalid values to parseGET_initialise
        sent no values
        '''
        # data required for testing
        current_time = datetime.now()
        month_start = datetime(year=current_time.year, month=current_time.month, day=1)
        #login using url to update the session variable
        self.client.login(username='jayalalv@default.com', password='solar')
        # sending valid values
        request = self.factory.get('/group/transactionList/', {
                                                                'tr': str(THIS_MONTH),
                                                                'ts': '2012-12-11',
                                                                'te': '2012-12-11',
                                                                'u': str(self.u1.pk),
                                                                'page': '1',
                                                                'rpp': '10'
                                                                })
        (start_time, end_time, timeRange, filter_user_id, page_no, txn_per_page) = parseGET_initialise(request)
        self.assertEqual(start_time, month_start)
        self.assertEqual(timeRange, THIS_MONTH)
        self.assertEqual(filter_user_id, self.u1.pk)
        self.assertEqual(page_no, DEFAULT_START_PAGE)
        self.assertEqual(txn_per_page, 10)
        # sending no values
        request = self.factory.get('/group/transactionList/', {
                                                                'ts': '2012-12-11',
                                                                'te': '2012-12-11',
                                                                'u': str(self.u1.pk),
                                                                })
        (start_time, end_time, timeRange, filter_user_id, page_no, txn_per_page) = parseGET_initialise(request)
        self.assertEqual(start_time, datetime(2012, 12, 11))
        self.assertEqual(end_time, datetime(2012, 12, 11))
        self.assertEqual(timeRange, CUSTOM_RANGE)
        self.assertEqual(filter_user_id, self.u1.pk)
        self.assertEqual(page_no, DEFAULT_START_PAGE)
        self.assertEqual(txn_per_page, DEFAULT_RPP)
        request = self.factory.get('/group/transactionList/', {
                                                                'tr': str(LAST_MONTH),
                                                                'u': str(self.u1.pk),
                                                                })
        (start_time, end_time, timeRange, filter_user_id, page_no, txn_per_page) = parseGET_initialise(request)
        # sending invalid values
        request = self.factory.get('/group/transactionList/', {
                                                                'tr': 'abcd',
                                                                'u': str(self.u1.pk),
                                                                })
        (start_time, end_time, timeRange, filter_user_id, page_no, txn_per_page) = parseGET_initialise(request)
        # sending invalid values
        request = self.factory.get('/group/transactionList/', {
                                                                'ts': 'abcd',
                                                                'u': str(self.u1.pk),
                                                                })
        (start_time, end_time, timeRange, filter_user_id, page_no, txn_per_page) = parseGET_initialise(request)

    def test_makeTransaction_group(TestCase):
        # TODO asser tat a direct acces to this ink redirets  to formlink
        # TODO verify in test the atr the row is creaTED;
        # TODO verify that if the <useris making a group txn> the category belogs to group
        # TODO personal transactio should have both categories
        # perform a valid and invalid txn with personal oerm alone TODO
        # perfoem a vlaid and invalid txn with group perm alone TODO
        # perfoem a valid adn invalid txn with both perm TODO
        pass
