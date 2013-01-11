from django.test import TestCase
from django.contrib.auth.models import User, Permission
from projectApp1.models import Membership, Group
from TransactionApp.models import Category, UserCategory, GroupCategory
from TransactionApp.__init__ import INCOME, BANK, EXPENSE, CREDIT, PRIVATE, PUBLIC, THIS_MONTH, LAST_MONTH, CUSTOM_RANGE, \
        ALL_TIME, DEFAULT_START_PAGE, DEFAULT_RPP
from TransactionApp.helper import parseGET_initialise, get_outstanding_amount, get_expense, get_personal_paid_amount, \
        parseGET_ordering
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
        response = self.client.get(
                                '/createCategory/0/',
                                {
                                    'name': 'SBI',
                                    'category_type': 1,
                                    'description': '',
                                    'privacy': '0',
                                    'created_by': u1.pk
                                }
                                )
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
        '''
        now we have a user category and group category of same name
        try creating again the same by trying to create the Category of the same name
        that will trigger creating UserCategory again
        assert that only one UserCategory is made
        '''
        # if a Usercategory exist do not create again eg user enter the name of an exitig category and tries to create again
        response = self.client.get(
                                '/createCategory/0/',
                                {
                                    'name': 'SBI',
                                    'category_type': 1,
                                    'description': '',
                                    'privacy': '0',
                                    'created_by': u1.pk
                                }
                                )
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
        # verify that no new UserCategory or GroupCaregory is created
        self.assertEqual(1, UserCategory.objects.all().count())
        self.assertEqual(1, GroupCategory.objects.all().count())

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
        self.assertEqual(end_time, datetime(2012, 12, 12))
        self.assertEqual(timeRange, CUSTOM_RANGE)
        self.assertEqual(filter_user_id, self.u1.pk)
        self.assertEqual(page_no, DEFAULT_START_PAGE)
        self.assertEqual(txn_per_page, DEFAULT_RPP)
        request = self.factory.get('/group/transactionList/', {
                                                                'tr': str(LAST_MONTH),
                                                                'u': str(self.u1.pk),
                                                                })
        (start_time, end_time, timeRange, filter_user_id, page_no, txn_per_page) = parseGET_initialise(request)
        # TODO
        # sending invalid values
        request = self.factory.get('/group/transactionList/', {
                                                                'tr': 'abcd',
                                                                'u': str(self.u1.pk),
                                                                })
        (start_time, end_time, timeRange, filter_user_id, page_no, txn_per_page) = parseGET_initialise(request)
        # TODO
        # sending invalid values
        request = self.factory.get('/group/transactionList/', {
                                                                'ts': 'abcd',
                                                                'u': str(self.u1.pk),
                                                                })
        (start_time, end_time, timeRange, filter_user_id, page_no, txn_per_page) = parseGET_initialise(request)
        # TODO
        request = self.factory.get('/group/transactionList/', {
                                                                'o': '1.2.3.4.5',
                                                                })
        (order_by_args, order_by_page_list) = parseGET_ordering(request)
        self.assertEqual(order_by_args, ['paid_user', 'amount', 'description', 'users_involved', 'transaction_time'])
        request = self.factory.get('/group/transactionList/', {
                                                                'o': '-1.-2.-3.-4.-5',
                                                                })
        (order_by_args, order_by_page_list) = parseGET_ordering(request)
        self.assertEqual(order_by_args, ['-paid_user', '-amount', '-description', '-users_involved', '-transaction_time'])

    def test_makeTransaction_group(self):
        # TODO asser tat a direct acces to this ink redirets  to formlink
        # TODO verify in test the atr the row is creaTED;
        # TODO verify that if the <useris making a group txn> the category belogs to group
        # TODO personal transactio should have both categories
        # perform a valid and invalid txn with personal oerm alone TODO
        # perfoem a vlaid and invalid txn with group perm alone TODO
        # perfoem a valid adn invalid txn with both perm TODO
        pass

    def test_calculator(self):
        response = self.client.post('/calculator/2+3*5/', follow=True)
        self.assertEqual(response.content, '17')


class TransctionsTestCase(TestCase):
    '''
    A group
    car
        jayalal
        ropo
        shakku
        kurian
        dash
    having default to categories
        Bills
        Food
    and corresponding grpup categories
    '''
    def setUp(self):

        self.factory = RequestFactory()
        self.u1 = User.objects.create_user(username="jayalalv@default.com", email="jayalalv@default.com", password="solar")
        self.u2 = User.objects.create_user(username="ropo@default.com", email="ropo@default.com", password="p")
        self.u3 = User.objects.create_user(username="shakku@default.com", email="shakku@default.com", password="p")
        self.u4 = User.objects.create_user(username="kurian@default.com", email="kurian@default.com", password="p")
        self.u5 = User.objects.create_user(username="dash@default.com", email="dash@default.com", password="p")

        self.u1.user_permissions.add(Permission.objects.get(codename='group_transactions'))

        self.g1 = Group.objects.create(name='car', description='just for the sake of testing', privacy=0, deleted=False)

        self.m1 = Membership.objects.create(group=self.g1, user=self.u1, administrator=True, positions='creator', amount_in_pool=0)
        self.m2 = Membership.objects.create(group=self.g1, user=self.u2, administrator=False, positions='', amount_in_pool=0)
        self.m3 = Membership.objects.create(group=self.g1, user=self.u3, administrator=False, positions='', amount_in_pool=0)
        self.m4 = Membership.objects.create(group=self.g1, user=self.u4, administrator=False, positions='', amount_in_pool=0)
        self.m5 = Membership.objects.create(group=self.g1, user=self.u5, administrator=False, positions='', amount_in_pool=0)

        self.c1 = Category.objects.create(name='Bills', category_type=EXPENSE, privacy=PRIVATE, created_by_id=self.u1.id,)
        self.c2 = Category.objects.create(name='Food', category_type=EXPENSE, privacy=PUBLIC, created_by_id=self.u1.id,)

        self.gc1 = GroupCategory.objects.create(group_id=self.g1.id, category=self.c1, initial_amount=0, current_amount=0, deleted=False)
        self.gc2 = GroupCategory.objects.create(group_id=self.g1.id, category=self.c2, initial_amount=0, current_amount=0, deleted=False)


    def test_make_transactions(self):
        '''
        case1: user just paid
        jay ->  kurian  |200    |Rent   |gc:Bills   |1988
                ropo
        case2: user paid and is also a payee
        dash >  dash    |1500   |e-bill |gc:Bills   |1989
                shkku
                jay
        case3: User is just a payee
        ropo >  jay     |400    |Pizza  |gc:Food    |1990
                shakku
                dash
                kurian
        assert
            GroupCategory.current_amount
            Membership.amount_in_pool
            get_outstanding_amount function
            get_expense function
        '''
        #login
        self.client.login(username="jayalalv@default.com", password="solar")
        session = self.client.session
        session['active_group'] = self.g1
        session.save()
        response = self.client.post(
                                '/makeTransaction/',
                                {
                                    'users_involved': [str(self.u4.id), str(self.u2.id)],
                                    'to_category': [str(self.c1.id)],
                                    'transaction_time': datetime(1988, 1, 1),
                                    'Submit': ['Submit'],
                                    'amount': '200',
                                    'paid_user': [str(self.u1.id)],
                                    'description': ['Rent']
                                }
                                )
        response = self.client.post(
                                '/makeTransaction/',
                                {
                                    'users_involved': [str(self.u1.id), str(self.u3.id), str(self.u5.id)],
                                    'to_category': [str(self.c1.id)],
                                    'transaction_time': datetime(1989, 1, 1),
                                    'Submit': ['Submit'],
                                    'amount': '1500',
                                    'paid_user': [str(self.u5.id)],
                                    'description': ['ebill']
                                }
                                )
        response = self.client.post(
                                '/makeTransaction/',
                                {
                                    'users_involved': [str(self.u1.id), str(self.u3.id), str(self.u4.id), str(self.u5.id)],
                                    'to_category': [str(self.c2.id)],
                                    'transaction_time': datetime(1990, 1, 1),
                                    'Submit': ['Submit'],
                                    'amount': '400',
                                    'paid_user': [str(self.u2.id)],
                                    'description': ['Food']
                                }
                                )
        self.m1 = Membership.objects.get(group=self.g1, user=self.u1)
        self.m2 = Membership.objects.get(group=self.g1, user=self.u2)
        self.m3 = Membership.objects.get(group=self.g1, user=self.u3)
        self.m4 = Membership.objects.get(group=self.g1, user=self.u4)
        self.m5 = Membership.objects.get(group=self.g1, user=self.u5)
        self.assertEqual(-400, self.m1.amount_in_pool)
        self.assertEqual(+300, self.m2.amount_in_pool)
        self.assertEqual(-600, self.m3.amount_in_pool)
        self.assertEqual(-200, self.m4.amount_in_pool)
        self.assertEqual(+900, self.m5.amount_in_pool)
        self.assertEqual(-400, get_outstanding_amount(self.g1.id, self.m1.id, end_time=datetime(2015, 1, 1)))
        self.assertEqual(+300, get_outstanding_amount(self.g1.id, self.m2.id))
        self.assertEqual(-600, get_outstanding_amount(self.g1.id, self.m3.id))
        self.assertEqual(-200, get_outstanding_amount(self.g1.id, self.m4.id))
        self.assertEqual(+900, get_outstanding_amount(self.g1.id, self.m5.id))
        self.assertEqual(+600, get_expense(self.g1.id, self.m1.id, datetime(1987, 1, 1), datetime(2011, 1, 1)))
        self.assertEqual(+100, get_expense(self.g1.id, self.m2.id, datetime(1987, 1, 1), datetime(2011, 1, 1)))
        self.assertEqual(+600, get_expense(self.g1.id, self.m3.id, datetime(1987, 1, 1), datetime(2011, 1, 1)))
        self.assertEqual(+200, get_expense(self.g1.id, self.m4.id, datetime(1987, 1, 1), datetime(2011, 1, 1)))
        self.assertEqual(+600, get_expense(self.g1.id, self.m5.id, datetime(1987, 1, 1), datetime(2011, 1, 1)))

        self.gc1 = GroupCategory.objects.get(group_id=self.g1.id, category=self.c1)
        self.gc2 = GroupCategory.objects.get(group_id=self.g1.id, category=self.c2)
        self.assertEqual(1700, self.gc1.current_amount)
        self.assertEqual(400, self.gc2.current_amount)
        '''
        create new users muru and gman one with group permission and other with both
        make a new category CITI
        make two UserCategories CITI and Food
        assert that
        userCategories are update properly
        muru -> jay     |700    |uc:CITI    |gc: Food
                ropo
                shakku
                kurian
                dash
                muru
                gman
        muru            |200    |uc: CITI   |uc: Food
        '''

        self.u6 = User.objects.create_user(username="murali@default.com", email="murali@default.com", password="p")
        self.u7 = User.objects.create_user(username="gman@default.com", email="gman@default.com", password="p")

        self.m6 = Membership.objects.create(group=self.g1, user=self.u6, administrator=False, positions='', amount_in_pool=0)
        self.m7 = Membership.objects.create(group=self.g1, user=self.u7, administrator=False, positions='', amount_in_pool=0)

        self.c3 = Category.objects.create(name='CITI', category_type=EXPENSE, privacy=PRIVATE, created_by_id=self.u1.id,)
        self.c4 = Category.objects.create(name='Food', category_type=EXPENSE, privacy=PRIVATE, created_by_id=self.u1.id,)

        self.uc3 = UserCategory.objects.create(user_id=self.u6.id, category=self.c3, initial_amount=0, current_amount=0, deleted=False)
        self.uc4 = UserCategory.objects.create(user_id=self.u6.id, category=self.c4, initial_amount=0, current_amount=0, deleted=False)

        self.u6.user_permissions.add(Permission.objects.get(codename='group_transactions'))
        self.u6.user_permissions.add(Permission.objects.get(codename='personal_transactions'))
        response = self.client.logout()
        self.client.login(username="murali@default.com", password="p")
        session = self.client.session
        session['active_group'] = self.g1
        session.save()

        response = self.client.post(
                                '/makeTransaction/',
                                {
                                    'users_involved': [
                                                        str(self.u1.id),
                                                        str(self.u2.id),
                                                        str(self.u3.id),
                                                        str(self.u4.id),
                                                        str(self.u5.id),
                                                        str(self.u6.id),
                                                        str(self.u7.id),
                                                    ],
                                    'group_checkbox': '',
                                    'from_category': [str(self.c3.id)],
                                    'to_category': [str(self.c2.id)],
                                    'transaction_time': datetime(1991, 1, 1),
                                    'Submit': ['Submit'],
                                    'amount': '700',
                                    'paid_user': [str(self.u6.id)],
                                    'description': ['Food']
                                }
                                )
        response = self.client.post(
                                '/makeTransaction/',
                                {
                                    'from_category': [str(self.c3.id)],
                                    'to_category': [str(self.c4.id)],
                                    'transaction_time': datetime(1992, 1, 1),
                                    'Submit': ['Submit'],
                                    'amount': '200',
                                    'paid_user': [str(self.u6.id)],
                                    'description': ['Food']
                                }
                                )
        self.m1 = Membership.objects.get(group=self.g1, user=self.u1)
        self.m2 = Membership.objects.get(group=self.g1, user=self.u2)
        self.m3 = Membership.objects.get(group=self.g1, user=self.u3)
        self.m4 = Membership.objects.get(group=self.g1, user=self.u4)
        self.m5 = Membership.objects.get(group=self.g1, user=self.u5)
        self.m6 = Membership.objects.get(group=self.g1, user=self.u6)
        self.m7 = Membership.objects.get(group=self.g1, user=self.u7)
        self.assertEqual(-500, self.m1.amount_in_pool)
        self.assertEqual(+200, self.m2.amount_in_pool)
        self.assertEqual(-700, self.m3.amount_in_pool)
        self.assertEqual(-300, self.m4.amount_in_pool)
        self.assertEqual(+800, self.m5.amount_in_pool)
        self.assertEqual(+600, self.m6.amount_in_pool)
        self.assertEqual(-100, self.m7.amount_in_pool)

        self.gc2 = GroupCategory.objects.get(group_id=self.g1.id, category=self.c2)
        self.uc3 = UserCategory.objects.get(user_id=self.u6.id, category=self.c3)
        self.uc4 = UserCategory.objects.get(user_id=self.u6.id, category=self.c4)
        self.assertEqual(1100, self.gc2.current_amount)
        self.assertEqual(-900, self.uc3.current_amount)
        self.assertEqual(-900, self.uc3.get_outstanding())  # ensure outstanding also gets the same value
        self.assertEqual(900, get_personal_paid_amount(self.u6.id))  # ensure outstanding also gets the same value
        self.assertEqual(200, self.uc4.current_amount)
