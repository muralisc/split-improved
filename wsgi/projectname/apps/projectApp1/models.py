from django.db import models
from django.contrib.auth.models import User
from django import forms


class Group(models.Model):
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=564)
    members = models.ManyToManyField(User, through='Membership', related_name='memberOfGroup')
    update_time = models.DateTimeField(auto_now_add=True, null=False, blank=True)
    privacy = models.CharField(max_length=64, null=False, blank=True)
    deleted = models.BooleanField(null=False, blank=True)

    def __unicode__(self):
        return Membership.objects.get(group=self, position='creator')

    def invite(self, sender, recievers, msg=''):
        for user in recievers:
            # if the to_user is not already a member of group then only create invite
            if (Membership.objects.filter(group=self).filter(user=user).count() == 0):
                Invite.objects.create(
                                    from_user=sender,
                                    to_user=user,
                                    group=self,
                                    unread=True,
                                    message=msg
                                    )
            else:
                pass
                # raise error| log


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group


class Invite(models.Model):
    from_user = models.ForeignKey(User, related_name='from_invite_set')
    to_user = models.ForeignKey(User, related_name='to_invite_set')
    group = models.ForeignKey(Group)
    unread = models.BooleanField(null=False, blank=True)
    time = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=256, null=True, blank=True)


class Notifiacation(models.Model):
    from_user = models.ForeignKey(User, related_name='from_notification_set')
    to_user = models.ForeignKey(User, related_name='to_notification_set')
    group = models.ForeignKey(Group)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    href = models.CharField(max_length=256, null=True, blank=True)
    message = models.CharField(max_length=256, null=True, blank=True)
    is_unread = models.BooleanField(null=False, blank=True)
    is_hidden = models.BooleanField(null=False, blank=True)


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
