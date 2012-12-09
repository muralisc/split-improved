import calendar
from datetime import datetime
from dateutil import parser
from TransactionApp.models import Category, Payee, Transaction
from TransactionApp.__init__ import THIS_MONTH, LAST_MONTH, CUSTOM_RANGE
from django.db.models import Sum
from django.db.models import Q


def import_from_snapshot():
    import json
    import itertools
    from projectApp1.models import Membership, Group
    from django.contrib.auth.models import User

    json_file = open('mysql_dump_snapsho')
    data = json.load(json_file)
    model_dict = dict()
    # group the jsonby model
    for key, g in itertools.groupby(data, key=lambda x: x["model"]):
        model_dict[key] = list(g)
    model_strings = ['TransactionsApp.users', 'TransactionsApp.groupstable', 'TransactionsApp.transactions', 'personalApp.categories', 'personalApp.transfers']
    # make a dictionalr of old_pk and new_pk from user model
    user_dict = dict()
    for temp in model_dict[model_strings[0]]:
        try:
            asd = User.objects.create_user(
                                    username=temp['fields']['email'],
                                    email=temp['fields']['email'],
                                    password='p'
                                    )
        except:
            asd = User.objects.get(
                                    username=temp['fields']['email'],
                                    )
        user_dict[str(temp['pk'])] = asd.id   # assign the new id here
    ######## groupstable
    group_dict = dict()
    for temp in model_dict[model_strings[1]]:
        asd = Group.objects.create(
                            name=temp['fields']['name'],
                            description="",
                            privacy=0,
                            deleted=temp['fields']['deleted']
                            )
        for i in temp['fields']['members']:
            Membership.objects.create(
                            group_id=asd.id,
                            user_id=user_dict[str(i)],
                            administrator=False,
                            positions="",
                            amount_in_pool=0,
                            deleted=temp['fields']['deleted']
                            )
        group_dict[str(temp['pk'])] = asd.id   # assign the new id here
    # from transactions table create a list of dictionaries
    for temp in model_dict[model_strings[2]]:
        asd = Transaction.objects.create(
                        paid_user_id=user_dict[str(temp['fields']['user_paid'])],
                        amount=temp['fields']['amount'],
                        description=temp['fields']['description'],
                        transaction_time=temp['fields']['timestamp'],
                        created_by_user_id=user_dict[str(temp['fields']['user_paid'])],
                        created_for_group_id=group_dict[str(temp['fields']['group'])],
                        deleted=temp['fields']['deleted']
                        )
        for i in temp['fields']['users_involved']:
            Payee.objects.create(
                                txn_id=asd.id,                                     # assign id from above
                                user_id=user_dict[str(i)],
                                outstanding_amount=-temp['fields']['amount'] / len(temp['fields']['users_involved']) if i != temp['fields']['user_paid'] else temp['fields']['amount'] - temp['fields']['amount'] / len(temp['fields']['users_involved']),
                                deleted=temp['fields']['deleted']
                                )
    # from categories create categories
    category_dict = dict()
    for temp in model_dict[model_strings[3]]:
        cat = 2 if (temp['fields']['category_type'] == 'leach') else 1
        asd = Category.objects.create(
                    name=temp['fields']['name'],
                    category_type=cat,
                    privacy=0,
                    created_by_id=user_dict[str(7)],
                    )
        category_dict[str(temp['pk'])] = asd.id    # assign the new id here
    # transfers
    for temp in model_dict[model_strings[4]]:
        Transaction.objects.create(
                                paid_user_id=user_dict[str(temp['fields']['userID'])],
                                amount=temp['fields']['amount'],
                                from_category_id=category_dict[str(temp['fields']['fromCategory'])],
                                description=temp['fields']['description'],
                                to_category_id=category_dict[str(temp['fields']['toCategory'])],
                                transaction_time=temp['fields']['timestamp'],
                                created_by_user_id=user_dict[str(temp['fields']['userID'])],
                                deleted=temp['fields']['deleted']
                                )
    # populate the outstanding_amount in Membership
    asd = Group.objects.get(name='PA303')
    for temp_user in asd.members.all():
        temp_mem = Membership.objects.get(group=asd, user=temp_user)
        temp_mem.amount_in_pool = get_outstanding_amount(asd, temp_user)
        temp_mem.save()
    json_file.close()


def get_outstanding_amount(group_id, user_id, end_time=None):
    '''
    get the net outstandin amount in a group till the timestamp specified
    '''
    if end_time is not None:
        time_filter = Q(transaction_time__lte=end_time)
    else:
        time_filter = Q()
    txn_filters = (
                Q(created_for_group_id=group_id) &          # filter the group
                Q(deleted=False) &                          # filter deleted
                Q(time_filter)                              # filter time
                )
    # Get the net of all the transaction in which user was not a Payee
    # i.e user just paid but did not have any expense towards the txn
    s1 = Transaction.objects.filter(
                        txn_filters
                    ).filter(
                        paid_user_id=user_id
                    ).exclude(
                        users_involved=user_id
                    ).aggregate(
                        Sum('amount')
                    )['amount__sum']
    # Get the net sum of all the expenses the user was a Payee
    s2 = Payee.objects.filter(
                        deleted=False
                    ).filter(
                        user_id=user_id
                    ).filter(
                        txn__id__in=list(Transaction.objects.values_list('id', flat=True).filter(txn_filters))
                    ).aggregate(
                        Sum('outstanding_amount')
                    )['outstanding_amount__sum']
    return s1 + s2


def get_expense(group_id, user_id, start_time, end_time):
    '''
    Helper function to get the expense in the given time frame
    '''
    s2t = sum([temp.get_expense(user_id) for temp in Transaction.objects.filter(
                    Q(created_for_group_id=group_id) &                                  # filter the group
                    Q(deleted=False) &                                                  # filter deleted
                    (Q(paid_user_id=user_id) | Q(users_involved__id__in=[user_id])) &   # for including all transaction to which user is conencted
                    Q(transaction_time__range=(start_time, end_time))
                    ).distinct()])
    return s2t


def parseGET_initialise(request):
    '''
    Helper function to parse the requestGET to
    populate variables
    start_time
    end_time
    '''
    # Defaults
    current_time = datetime.now()
    month_start = datetime(year=current_time.year, month=current_time.month, day=1)
    start_time = month_start
    end_time = current_time
    timeRange = THIS_MONTH                                                                      # for angularjs
    # time range
    if 'tr' in request.GET:
        if int(request.GET['tr']) == THIS_MONTH:
            start_time = datetime(year=current_time.year, month=current_time.month, day=1)      # end_time is alredy initialised
            timeRange = THIS_MONTH                                                              # for angularjs
        elif int(request.GET['tr']) == LAST_MONTH:
            start_time = datetime(year=current_time.year, month=current_time.month - 1, day=1)
            timeRange = LAST_MONTH                                                              # for angularjs
            end_time = datetime(
                        year=current_time.year,
                        month=current_time.month,
                        day=1)
                        #day=calendar.monthrange(current_time.year, current_time.month - 1)[1])
    elif 'ts' in request.GET or 'te' in request.GET:
        timeRange = CUSTOM_RANGE                                                                # for angularjs
        # time start
        if 'ts' in request.GET:
            start_time = parser.parse(request.GET['ts'])
        # time end
        if 'te' in request.GET:
            end_time = parser.parse(request.GET['te'])
    if 'u' in request.GET:
        filter_user_id = int(request.GET['u'])
    else:
        filter_user_id = request.user.pk
    if 'page' in request.GET:
        page_no = int(request.GET['page'])
    else:
        page_no = 1
    if 'rpp' in request.GET:
        txn_per_page = int(request.GET['rpp'])
    else:
        txn_per_page = 5
    return (start_time, end_time, timeRange, filter_user_id, page_no, txn_per_page)
