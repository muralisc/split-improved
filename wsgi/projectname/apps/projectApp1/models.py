from django.db import models
from django.contrib.auth.models import User
from django import forms


class MyUser(User):
    class Meta:
        proxy = True

    def do_something(self):
        pass


class Group(models.Model):
    PRIVATE = 0
    PUBLIC = 1
    PRIVACY_CHOICES = (
                        (PRIVATE, 'private'),
                        (PUBLIC, 'public'),
                        )
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=564, blank=True)
    members = models.ManyToManyField(User, through='Membership', related_name='memberOfGroup')
    create_time = models.DateTimeField(auto_now_add=True)
    privacy = models.IntegerField(choices=PRIVACY_CHOICES)
    deleted = models.BooleanField(null=False, blank=True)

    def __unicode__(self):
        return '{0}'.format(self.name)

    def invite(self, sender, recievers, msg=''):
        '''
        Sent invites to the recievers specified from the sender for "this" group
        '''
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
                # raise error| log TODO


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
    deleted = models.BooleanField(null=False, blank=True)

    def __unicode__(self):
        return '{1} for {0}'.format(self.group.name, self.to_user.username)


class Notification(models.Model):
    from_user = models.ForeignKey(User, related_name='from_notification_set')
    to_user = models.ForeignKey(User, related_name='to_notification_set')
    group = models.ForeignKey(Group)
    create_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    href = models.CharField(max_length=256, null=True, blank=True)
    message = models.CharField(max_length=1000, null=True, blank=True)
    is_unread = models.BooleanField(null=False, blank=True)
    is_hidden = models.BooleanField(null=False, blank=True)
    deleted = models.BooleanField(null=False, blank=True)

    def __unicode__(self):
        return '{0}--{1}'.format(self.from_user, self.to_user)

    def get_time(self):
        """
        formats creted_time
        """
        from datetime import datetime
        import pytz
        time_passed = datetime.now(pytz.UTC) - self.create_time
        if (time_passed.days < 7):
            if (time_passed.days == 0):
                hours, seconds = divmod(time_passed.seconds, 3600)
                if (hours == 0):
                    minutes, dont_want = divmod(seconds, 60)
                    if(minutes == 0):
                        time_string = "{0} seconds ago".format(dont_want)
                    else:
                        time_string = "{0} minutes ago".format(minutes)
                elif (hours == 1):
                    time_string = "an hour ago"
                else:
                    time_string = "{0} hours ago".format(hours)
            elif (time_passed.days == 1):
                time_string = "Yesterday "
            else:
                time_string = "{0} days ago".format(time_passed.days)
        elif(time_passed.days < 150):
            time_string = self.create_time.strftime('%b %d %H:%M')
        else:
            time_string = self.create_time.strftime('%Y,%b %d')
        return time_string


class Membership(models.Model):
    '''
    Table releating User with Group
    '''
    group = models.ForeignKey(Group, related_name='getMemberships')
    user = models.ForeignKey(User)
    administrator = models.BooleanField(null=False, blank=True)
    positions = models.CharField(max_length=64)
    amount_in_pool = models.FloatField()
    create_time = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(null=False, blank=True)

    def __unicode__(self):
        return "{0}|{1}".format(self.group.name, self.user.username)
