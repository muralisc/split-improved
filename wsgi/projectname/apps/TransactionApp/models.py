from django.db import models
from django.contrib.auth.models import User
from projectApp1.models import Group
from django import forms


class Category(models.Model):
    INCOME = 0
    BANK = 1
    EXPENSE = 2
    CREDIT = 3
    PRIVATE = 0
    PUBLIC = 1
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
    users = models.ManyToManyField(User, through='UserCategory', related_name='usesCategories')     # all the users who use this category
    groups = models.ManyToManyField(Group, through='GroupCategory', related_name='usesCategories')  # all the groups that use this this catgory

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
        return '{0}|{1}'.format(self.user.username, self.category.name)


class Transaction(models.Model):
    paid_user = models.ForeignKey(User, related_name='paidForTransaction')
    amount = models.FloatField()
    from_category = models.ForeignKey(Category, related_name='inFromfield', null=True, blank=True)
    description = models.CharField(max_length=256, null=True, blank=True)
    to_category = models.ForeignKey(Category, related_name='inToField', null=False, blank=True)
    users_involved = models.ManyToManyField(User, through='Payee', related_name='involvedInTransactions', blank=True)
    transaction_time = models.DateTimeField(null=False, blank=True)
    create_time = models.DateTimeField(auto_now_add=True, null=False, blank=True)
    created_by_user = models.ForeignKey(User, related_name='ceatedTransaction', null=False, blank=True)
    created_for_group = models.ForeignKey(Group, null=True, blank=True)
    history = models.OneToOneField('Transaction', null=True, blank=True)
    deleted = models.BooleanField(null=False, blank=True)

    class Meta:
            permissions = (
                ("group_transactions", "Can make group transactions"),
                ("personal_transactions", "Can make personal transactions"),
            )

    def __unicode__(self):
        pass
        return '{0} | {1} | {2}'.format(self.paid_user, self.amount, self.created_for_group)

    def associatePayees(self, payee_list):
        no_of_payees = len(payee_list)
        for temp_payee in payee_list:
            # if it doestnt already exist
            temp_cost = -self.amount / no_of_payees
            if(temp_payee.id == self.paid_user.id):
                temp_cost = self.amount + temp_cost
            Payee.objects.create(txn_id=self.id, user_id=temp_payee.id, outstanding_amount=temp_cost)


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
        exclude = ('created_by_user',
                   'created_for_group',
                   'deleted')


class Payee(models.Model):
    '''
    Table relating User table with Transaction table
    contains all the users involved in the transaction[not the paid user]
    with the respective amount outstanding
    '''
    txn = models.ForeignKey(Transaction)
    user = models.ForeignKey(User)
    outstanding_amount = models.FloatField()
