from django.db import models
from django.contrib.auth.models import Permission, User
from django import forms


class Group(models.Model):
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=564)
    members = models.ManyToManyField(User, through='Membership', related_name='memberOfGroup')
    update_time = models.DateTimeField(auto_now_add=True, null=False, blank=True)
    privacy = models.CharField(max_length=64, null=False, blank=True)
    deleted = models.BooleanField(null=False, blank=True)

    def __unicode__(self):
        return self.name


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group


class Membership(models.Model):
    '''
    Table releating User with Group
    '''
    grp = models.ForeignKey(Group)
    usr = models.ForeignKey(User)
    administrator = models.BooleanField(null=False, blank=True)
    positions = models.CharField(max_length=64)
    amount_in_pool = models.IntegerField()

    def __unicode__(self):
        return "{0}|  {1}".format(self.grp.name, self.usr.username)


class Category(models.Model):
    name = models.CharField(max_length=6)
    category_type = models.CharField(max_length=64)
    initial_amount = models.IntegerField(null=False, blank=True)
    created_by_user = models.ForeignKey(User, related_name='createdCategory', null=False, blank=True)
    created_for_group = models.ForeignKey(Group, null=False, blank=True)
    deleted = models.BooleanField(null=False, blank=True)


class Transaction(models.Model):
    paid_user = models.ForeignKey(User, related_name='paidForTransaction')
    amount = models.IntegerField()
    from_category = models.ForeignKey(Category, related_name='inFromfield', null=False, blank=True)
    description = models.TextField(null=True, blank=True)
    to_category = models.ForeignKey(Category, related_name='inToField', null=False, blank=True)
    users_involved = models.ManyToManyField(User, through='Payee', related_name='involvedInTransactions')
    date = models.DateTimeField(auto_now_add=True, null=False, blank=True)
    created_by_user = models.ForeignKey(User, related_name='ceatedTransaction', null=False, blank=True)
    created_for_group = models.ForeignKey(Group, null=False, blank=True)
    deleted = models.BooleanField(null=False, blank=True)

    class Meta:
            permissions = (
                ("group_transactions", "Can make group transactions"),
                ("personal_transactions", "Can make personal transactions"),
            )


class Payee(models.Model):
    '''
    Table relating User table with Transaction table
    '''
    txn = models.ForeignKey(Transaction)
    user = models.ForeignKey(User)
    cost = models.IntegerField()
