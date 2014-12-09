# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import authenticate
from .models import User
import json
import jpush
from jpush.conf import app_key, master_secret

# 注册
def register(request):
	if request.method == 'POST':
		response = {}
		username = request.POST['username']
		nickname = request.POST['nickname']
		password = request.POST['password']
		try:
			user = User.objects.get(username=username)
			# code = 1: 用户名已存在
			response['code'] = 1
			return HttpResponse(json.dumps(response), content_type="application/json")
		except:
			user = User.objects.create_user(username=username, nickname=nickname, password=password)
			# code = 0: OK
			response['code'] = 0
			return HttpResponse(json.dumps(response), content_type="application/json")
	else:
		return HttpResponse("This should be done in a POST method!")

# 登录
def login(request):
	if request.method == 'POST':
		# 用户名不存在
		response = {'code': 1}
		username = request.POST['username']
		password = request.POST['password']
		try:
			user = User.objects.get(username=username)
			# 验证密码正确性
			if user.check_password(password):
				# code = 0: OK
				response['code'] = 0
				# 创建session
				request.session['onlineuser'] = username
				return HttpResponse(json.dumps(response), content_type="application/json")
			else:
				# code = 2: 密码错误
				response['code'] = 2
				return HttpResponse(json.dumps(response), content_type="application/json")
		except:
			return HttpResponse(json.dumps(response), content_type="application/json")
	else:
		return HttpResponse("This should be done in a POST method!")

# 注销
def logout(request):
	if request.method == 'POST':
		try:
			response = {'code': 0}
			del request.session['onlineuser']
		except:
			pass
		return HttpResponse(json.dumps(response), content_type="application/json")
	else:
		return HttpResponse("This should be done in a POST method!")

# 添加好友
def add(request):
	if request.method == 'POST':
		username = request.POST['username']
		target = request.POST['target']
		# code = 1: 目标用户名不存在
		response = {'code': 1}
		userinfo = request.session.get('onlineuser', None)
		# 验证是否已登录
		if userinfo:
			try:
				user1 = User.objects.get(username=username)
				user2 = User.objects.get(username=target)
				user1.friends.add(user2)
				# code = 0: OK
				response['code'] = 0
				return HttpResponse(json.dumps(response), content_type="application/json")
			except:
				return HttpResponse(json.dumps(response), content_type="application/json")
		else:
			# code = 2: 用户未登录
			response['code'] = 2
			return HttpResponse(json.dumps(response), content_type="application/json")
	else:
		return HttpResponse("This should be done in a POST method!")

# 心跳包
def heartbeat(request):
	if request.method == 'POST':
		return HttpResponse()
	else:
		return HttpResponse("This should be done in a POST method!")

# 搜索好友列表
def search(request):
	if request.method == 'POST':
		username = request.POST['username']
		# code = 1: 用户名不存在
		response = {'code': 1}
		userinfo = request.session.get('onlineuser', None)
		# 验证是否已登录
		if userinfo:
			try:
				user = User.objects.get(username=username)
				list = user.friends.all()
				response = {'count': len(list)}
				fri_list = []
				for i in list:
					fri_list.append({'nickname': i.username})
				response['user'] = fri_list
				return HttpResponse(json.dumps(response), content_type="application/json")
			except:
				return HttpResponse(json.dumps(response), content_type="application/json")
		else:
			# code = 2: 用户未登录
			response['code'] = 2
			return HttpResponse(json.dumps(response), content_type="application/json")
	else:
		return HttpResponse("This should be done in a POST method!")
		
# 发送消息
def send(request):
	if request.method == 'POST':
		username = request.POST['username']
		target = request.POST['target']
		msg = request.POST['msg']
		# code = 1: 目标用户名不存在
		response = {'code': 1}
		userinfo = request.session.get('onlineuser', None)
		# 验证是否已登录
		if userinfo:
			try:
				user = User.objects.get(username=target)
				_jpush = jpush.JPush(app_key, master_secret)
				push = _jpush.create_push()
				push.audience = jpush.audience(jpush.alias(target))
				android_msg = jpush.android(alert=msg, title="From "+username)
				push.notification = jpush.notification(alert=msg, android=android_msg)
				push.platform = jpush.all_
				push.send()
				# code = 0: OK
				response['code'] = 0
				return HttpResponse(json.dumps(response), content_type="application/json")
			except:
				return HttpResponse(json.dumps(response), content_type="application/json")
		else:
			# code = 2: 用户未登录
			response['code'] = 2
			return HttpResponse(json.dumps(response), content_type="application/json")
	else:
		return HttpResponse("This should be done in a POST method!")