from django.db import models
from django.contrib.auth.models import User
from django import forms


class Group(models.Model):
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=564, blank=True)
    members = models.ManyToManyField(User, through='Membership', related_name='memberOfGroup')
    create_time = models.DateTimeField(auto_now_add=True)
    privacy = models.CharField(max_length=64, null=False, blank=True)
    deleted = models.BooleanField(null=False, blank=True)

    def __unicode__(self):
        return '{0}'.format(self.name)

    def invite(self, sender, recievers, msg=''):
        for user in recievers:
            # if the to_user is not already a member/invited of group then only create invite
            if not Invite.objects.filter(group=self).filter(to_user=user).exists():
                if not Membership.objects.filter(group=self).filter(user=user).exists():
                    Invite.objects.create(
                                        from_user=sender,
                                        to_user=user,
                                        group=self,
                                        unread=True,
                                        message=msg
                                        )
                else:
                    pass
            else:
                pass
                # raise error| log


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        exclude = ('members',)


class Invite(models.Model):
    from_user = models.ForeignKey(User, related_name='from_invite_set')
    to_user = models.ForeignKey(User, related_name='to_invite_set')
    group = models.ForeignKey(Group)
    unread = models.BooleanField(null=False, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=256, null=True, blank=True)

    def __unicode__(self):
        return '{0}|{1}'.format(self.group.name, self.to_user.username)


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
    group = models.ForeignKey(Group, related_name='getMemberships')
    user = models.ForeignKey(User)
    administrator = models.BooleanField(null=False, blank=True)
    positions = models.CharField(max_length=64)
    amount_in_pool = models.IntegerField()

    def __unicode__(self):
        return "{0}|{1}".format(self.group.name, self.user.username)
