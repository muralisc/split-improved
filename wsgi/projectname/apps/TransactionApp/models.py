from django.db import models
from django.contrib.auth.models import User
from TransactionApp.__init__ import INCOME, BANK, EXPENSE, CREDIT, PRIVATE, PUBLIC
from projectApp1.models import Group, Notification
from django import forms
from django.db.models import Sum


class Category(models.Model):
    ACCOUNT_TYPE = (
                    (INCOME, 'income'),
                    (BANK, 'bank'),
                    (EXPENSE, 'expense'),
                    (CREDIT, 'credit'),
                    )
    name = models.CharField(max_length=255)
    category_type = models.IntegerField(choices=ACCOUNT_TYPE)
    description = models.CharField(max_length=564, null=True, blank=True)
    privacy = models.IntegerField(
                                    choices=(
                                            (PRIVATE, 'private'),
                                            (PUBLIC, 'public'),
                                            ),
                                    )
    created_by = models.ForeignKey(User)
    create_time = models.DateTimeField(auto_now_add=True)
    users = models.ManyToManyField(User, through='UserCategory', related_name='usesCategories')
    groups = models.ManyToManyField(Group, through='GroupCategory', related_name='usesCategories')
    deleted = models.BooleanField(null=False, blank=True)

    def __unicode__(self):
        return '{0} | {1}'.format(self.name, self.ACCOUNT_TYPE[self.category_type][1])


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        widgets = {
                  }
        exclude = ('created_by',
                   'created_by_id',
                   'date',
                   'users',
                   'groups',
                   )


class GroupCategory(models.Model):
    '''
    Table relating groups with categories
    '''
    group = models.ForeignKey(Group)
    category = models.ForeignKey(Category)
    initial_amount = models.IntegerField(null=False, blank=True)
    current_amount = models.IntegerField(null=False, blank=True)
    create_time = models.DateTimeField(auto_now_add=True, null=False, blank=True)
    deleted = models.BooleanField(null=False, blank=True)

    def __unicode__(self):
        return '{0}|{1}'.format(self.group.name, self.category.name)


class UserCategory(models.Model):
    '''
    Table relating users with categories
    '''
    user = models.ForeignKey(User)
    category = models.ForeignKey(Category)
    initial_amount = models.IntegerField(null=False, blank=True)
    current_amount = models.IntegerField(null=False, blank=True)
    create_time = models.DateTimeField(auto_now_add=True, null=False, blank=True)
    deleted = models.BooleanField(null=False, blank=True)

    def __unicode__(self):
        return '{0}'.format(self.category.name)

    def get_outstnading(self):
        category_lost = Transaction.objects.filter(
                                        from_category_id=self.category.id,
                                        paid_user_id=self.user_id,
                                    ).aggregate(
                                        Sum('amount')
                                    )['amount__sum']
        category_lost = category_lost if category_lost else 0
        category_gained = Transaction.objects.filter(
                                        to_category_id=self.category.id,
                                        paid_user_id=self.user_id,
                                    ).aggregate(
                                        Sum('amount')
                                    )['amount__sum']
        category_gained = category_gained if category_gained else 0
        return category_gained - category_lost + self.initial_amount


class Transaction(models.Model):
    '''
     DEFINITIONS
     involved user: may be a payee or paid_user
     payees
     paid : zero or positive only , actual money given, for all users involved
     outstanding: postove or negative, non zero for all users
     expense: zero or positive for all users involved
    '''
    paid_user = models.ForeignKey(User, related_name='paidForTransaction')
    amount = models.FloatField()
    from_category = models.ForeignKey(Category, related_name='inFromfield', null=True, blank=True)
    description = models.CharField(max_length=256, null=True, blank=True)
    to_category = models.ForeignKey(Category, related_name='inToField', null=True, blank=True)
    users_involved = models.ManyToManyField(User, through='Payee', related_name='involvedInTransactions', blank=True)
    transaction_time = models.DateTimeField(null=False, blank=True)
    create_time = models.DateTimeField(auto_now_add=True, null=False, blank=True)
    created_by_user = models.ForeignKey(User, related_name='ceatedTransaction', null=False, blank=True)
    created_for_group = models.ForeignKey(Group, null=True, blank=True)
    history = models.OneToOneField('Transaction', null=True, blank=True, related_name='future')
    deleted = models.BooleanField(null=False, blank=True)

    class Meta:
            permissions = (
                ("group_transactions", "Can make group transactions"),
                ("personal_transactions", "Can make personal transactions"),
            )

    def __unicode__(self):
        return '{0}'.format(self.id)

    def get_outstanding_amount(self, user_id):
        '''
        get the outstanding amouth of the "user" in "this" txn
        '''
        user_cost = 0
        try:
            temp_payee = Payee.objects.get(txn=self, user_id=user_id)
            user_cost = temp_payee.outstanding_amount
        except Payee.DoesNotExist:
            if self.paid_user_id == user_id:
                user_cost = self.amount
            else:
                # log it that an invalid user tried to TODO`
                pass
        return user_cost

    def get_expense(self, user_id):
        if Payee.objects.filter(txn=self).filter(user_id=user_id).exists():
            ost_amt = Payee.objects.get(txn=self, user_id=user_id).outstanding_amount
            return (self.amount - ost_amt) if (ost_amt > 0) else abs(ost_amt)
        else:
            return 0

    def associatePayees(self, payee_list):
        '''
        To create Payee objects for the transaction
        '''
        no_of_payees = len(payee_list)
        for temp_payee in payee_list:
            # if it doestnt already exist TODO
            temp_cost = -self.amount / no_of_payees
            if(temp_payee.id == self.paid_user.id):
                temp_cost = self.amount + temp_cost
            Payee.objects.create(txn_id=self.id, user_id=temp_payee.id, outstanding_amount=temp_cost)

    def create_notifications(self, user_created_id, notification_type):
        # TODO make help string for this function
        # TODO test to ensuer that the trasaction craing user dont have a txn
        payee_objects = Payee.objects.filter(txn_id=self.id, deleted=False)
        for p_object in payee_objects:
            if p_object.user_id != user_created_id:
                if notification_type == 'txn_created':
                    message = 'created transaction for {0}/{1}; \
                            your outstanding is <strong>{2:.2f}</strong> \
                            among {3} users involved '.format(
                                self.description, self.to_category,
                                p_object.outstanding_amount,
                                self.users_involved.count()
                                )
                elif notification_type == 'txn_deleted':
                    message = 'deleted transaction for {0}/{1}; \
                            your outstanding is <strong>{2:.2f}</strong> \
                            among {3} users involved '.format(
                                self.description, self.to_category,
                                p_object.outstanding_amount,
                                self.users_involved.count()
                                )
                elif notification_type == 'txn_edited':
                    message = 'edited transaction for {0}/{1}; \
                            your outstanding is <strong>{2:.2f}</strong> \
                            among {3} users involved '.format(
                                self.description, self.to_category,
                                p_object.outstanding_amount,
                                self.users_involved.count()
                                )
                # create notficatin for all the payees
                if p_object.user.id != user_created_id:
                    Notification.objects.create(
                                        from_user_id=user_created_id,
                                        to_user_id=p_object.user.id,
                                        group_id=self.created_for_group.id,
                                        href=self.id,
                                        message=message,
                                        is_unread=True,
                                        is_hidden=False,
                                        deleted=False,
                                                )
        # create notification for the user paid
        if self.paid_user_id != user_created_id:
            message = 'edited transaction for {0}/{1}; \
                    your outstanding is <strong>{2:.2f}</strong> \
                    among {3} users involved '.format(
                        self.description, self.to_category,
                        self.get_outstanding_amount(self.paid_user_id),
                        self.users_involved.count()
                        )
            Notification.objects.create(
                                from_user_id=user_created_id,
                                to_user_id=self.paid_user_id,
                                group_id=self.created_for_group.id,
                                href=self.id,
                                message=message,
                                is_unread=True,
                                is_hidden=False,
                                deleted=False,
                                        )


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        widgets = {
                    'paid_user': forms.Select(attrs={'class': ''}),
                    'amount': forms.TextInput(attrs={'placeholder': 'Amount', 'class': ''}),
                    'description': forms.TextInput(attrs={'placeholder': 'Description', 'class': ''}),
                    'users_involved': forms.CheckboxSelectMultiple(),
                    'date': forms.TextInput(attrs={'placeholder': 'Date', 'class': ''}),
                  }
        exclude = (
                    'created_by_user',
                    'created_for_group',
                    'history',
                    'deleted',
                   )


class Payee(models.Model):
    '''
    Table relating User table with Transaction table
    contains all the users involved in the transaction[not the paid user]
    with the respective amount outstanding
    '''
    txn = models.ForeignKey(Transaction)
    user = models.ForeignKey(User)
    outstanding_amount = models.FloatField()
    deleted = models.BooleanField(null=False, blank=True)

    def __unicode__(self):
        return '{0} | {1}'.format(self.user, self.outstanding_amount)
