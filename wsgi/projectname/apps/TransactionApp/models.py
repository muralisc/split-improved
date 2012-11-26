from django.db import models
from django.contrib.auth.models import User
from projectApp1.models import Group
from django import forms

class Category(models.Model):
    name = models.CharField(max_length=6)
    category_type = models.CharField(max_length=64)
    initial_amount = models.IntegerField(null=False, blank=True)
    created_by_user = models.ForeignKey(User, related_name='createdCategory', null=False, blank=True)
    created_for_group = models.ForeignKey(Group, null=True, blank=True)
    deleted = models.BooleanField(null=False, blank=True)

    def __unicode__(self):
        return self.name


class Transaction(models.Model):
    paid_user = models.ForeignKey(User, related_name='paidForTransaction')
    amount = models.IntegerField()
    from_category = models.ForeignKey(Category, related_name='inFromfield', null=False, blank=True)
    description = models.CharField(max_length=256, null=True, blank=True)
    to_category = models.ForeignKey(Category, related_name='inToField', null=False, blank=True)
    users_involved = models.ManyToManyField(User, through='Payee', related_name='involvedInTransactions')
    date = models.DateTimeField(null=False, blank=True)
    created_by_user = models.ForeignKey(User, related_name='ceatedTransaction', null=False, blank=True)
    created_for_group = models.ForeignKey(Group, null=True, blank=True)
    deleted = models.BooleanField(null=False, blank=True)

    class Meta:
            permissions = (
                ("group_transactions", "Can make group transactions"),
                ("personal_transactions", "Can make personal transactions"),
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
        exclude = ('created_by_user',
                   'created_for_group',
                   'deleted')


class Payee(models.Model):
    '''
    Table relating User table with Transaction table
    '''
    txn = models.ForeignKey(Transaction)
    user = models.ForeignKey(User)
    cost = models.IntegerField()