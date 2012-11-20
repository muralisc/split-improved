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
    group = models.ForeignKey(Group)
    user = models.ForeignKey(User)
    administrator = models.BooleanField(null=False, blank=True)
    positions = models.CharField(max_length=64)
    amount_in_pool = models.IntegerField()

    def __unicode__(self):
        return "{0}|  {1}".format(self.group.name, self.user.username)


