# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser

# Create your models here.
class UserManager(BaseUserManager):

  def create_user(self, username, nickname, password=None):
	user = self.model(
	  username=username,
	  nickname=nickname,
	)
	user.set_password(password)
	user.save(using=self._db)
	return user

  def create_superuser(self, username, nickname, password):
	user = self.create_user(username, nickname, password)
	user.is_admin = True
	user.save(using=self._db)
	return user
	
class User(AbstractBaseUser):
	username = models.CharField(max_length=30, unique=True, db_index=True)
	nickname = models.CharField(max_length=100)
	mobile = models.CharField(max_length=100, null=True, unique=True, db_index=True)
	is_admin = models.BooleanField(default=False)
	friends = models.ManyToManyField('self')
	
	USERNAME_FIELD = 'username'
	objects = UserManager()

	def get_full_name(self):
		return self.nickname

	def get_short_name(self):
		return self.nickname
  
	def __unicode__(self):
		return self.username