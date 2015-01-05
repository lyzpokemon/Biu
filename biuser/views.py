# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import authenticate
from .models import User
from math import radians, tan
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
		#if userinfo:
		try:
			user1 = User.objects.get(username=username)
			user2 = User.objects.get(username=target)
			user1.friends.add(user2)
			# code = 0: OK
			response['code'] = 0
			return HttpResponse(json.dumps(response), content_type="application/json")
		except:
			return HttpResponse(json.dumps(response), content_type="application/json")
		#else:
		# code = 2: 用户未登录
		#	response['code'] = 2
		#	return HttpResponse(json.dumps(response), content_type="application/json")
	else:
		return HttpResponse("This should be done in a POST method!")

# 心跳包
def heartbeat(request):
	if request.method == 'POST':
		username = request.POST['username']
		latitude = request.POST['latitude']
		longitude = request.POST['longitude']
		User.objects.filter(username=username).update(latitude=latitude, longitude=longitude)
		return HttpResponse()
	else:
		return HttpResponse("This should be done in a POST method!")

# 判断两浮点数是否在误差范围内相等
def equal(a, b, error):
	return abs(a-b) < error

# 判断目标节点坐标相对原始坐标方向是否正确
def isrightdir(dir, x0, y0, x, y):
	if (0 <= dir <= 90) and (x0 >= x or y0 >= y):
		return False
	if (90 <= dir <= 180) and (x0 <= x or y0 >= y):
		return False
	if (180 <= dir <= 270) and (x0 <= x or y0 <= y):
		return False
	if (270 <= dir <= 360) and (x0 >= x or y0 <= y):
		return False
	return True

# 判断为垂直或平行方向时目标坐标在误差范围内是否在直线上
def isbiued_special(dir, x0, y0, x, y, error):
	if equal(dir, 90, 1e-2):
		return (y0 <= y) and equal(x0, x, error)
	if equal(dir, 270, 1e-2):
		return (y0 >= y) and equal(x0, x, error)
	if (equal(dir, 0, 1e-2) or equal(dir, 360, 1e-2)):
		return (x0 <= x) and equal(y0, y, error)
	if equal(dir, 180, 1e-2):
		return (x0 >= x) and equal(y0, y, error)
	return False
	
# 判断为垂直或平行方向时目标坐标在误差范围内是否在直线上
def isbiued_special_debug(dir, x0, y0, x, y, error_xy, error):
	if equal(dir, 90, error_xy):
		return (y0 <= y) and equal(x0, x, error)
	if equal(dir, 270, error_xy):
		return (y0 >= y) and equal(x0, x, error)
	if (equal(dir, 0, error_xy) or equal(dir, 360, error_xy)):
		return (x0 <= x) and equal(y0, y, error)
	if equal(dir, 180, error_xy):
		return (x0 >= x) and equal(y0, y, error)
	return False

# 判断目标坐标是否在直线上
def isbiued(dir, k, b, user_a, user_b, error):
	x0 = user_a.longitude
	y0 = user_a.latitude
	x = user_b.longitude
	y = user_b.latitude
	return isrightdir(dir, x0, y0, x, y) and equal(k * x + b, y, error)
	
# 返回biu中目标列表
def search(request):
	if request.method == 'POST':
		username = request.POST['username']
		direction = float(request.POST['direction'])
		# code = 1: 用户名不存在
		response = {'code': 1}
		userinfo = request.session.get('onlineuser', None)
		# 验证是否已登录
		#if userinfo:
		try:
			users = User.objects.all();
			user = users.get(username=username)
			user_list = users.exclude(username=username)
			# 换算为平面坐标角度
			direction = (-direction + 360 + 90) % 360
			# 斜率
			k = tan(radians(direction))
			# b = y - kx
			b = user.latitude - k * user.longitude
			biued_list = []
			# 方向直线是垂线或水平线
			if (equal(direction, 90, 1e-3) or equal(direction, 270, 1e-3) or equal(direction, 0, 1e-3) or equal(direction, 360, 1e-3) or equal(direction, 180, 1e-3)):
				for i in user_list:
					if isbiued_special(direction, user.longitude, user.latitude, i.longitude, i.latitude, 1e-2):
						biued_list.append({'nickname': i.username})
						try:
							send_msg(username=username, target=i.username, title="Biu", msg="You are BIUed by " + username + " !")
						except Exception, e:
							print e
			# 其它
			else:
				for i in user_list:
					if isbiued(direction, k, b, user, i, 1e-2):
						biued_list.append({'nickname': i.username})
						try:
							send_msg(username=username, target=i.username, title="Biu", msg="You are BIUed by " + username + " !")
						except Exception, e:
							print e
			response = {'count': len(biued_list)}
			response['users'] = biued_list
			response['code'] = 0
			return HttpResponse(json.dumps(response), content_type="application/json")
		except Exception, e:
			print e
			return HttpResponse(json.dumps(response), content_type="application/json")
		#else:
			# code = 2: 用户未登录
			#response['code'] = 2
			#return HttpResponse(json.dumps(response), content_type="application/json")
	else:
		return HttpResponse("This should be done in a POST method!")

# 返回好友列表
def friends(request):
	if request.method == 'POST':
		username = request.POST['username']
		# code = 1: 用户名不存在
		response = {'code': 1}
		userinfo = request.session.get('onlineuser', None)
		# 验证是否已登录
		#if userinfo:
		try:
			user = User.objects.get(username=username)
			list = user.friends.all()
			response = {'count': len(list)}
			fri_list = []
			for i in list:
				fri_list.append({'nickname': i.username})
			response['users'] = fri_list
			return HttpResponse(json.dumps(response), content_type="application/json")
		except:
			return HttpResponse(json.dumps(response), content_type="application/json")
		#else:
			# code = 2: 用户未登录
			#response['code'] = 2
			#return HttpResponse(json.dumps(response), content_type="application/json")
	else:
		return HttpResponse("This should be done in a POST method!")
		
# 带参发送消息
def send_msg(username, target, title, msg):
	_jpush = jpush.JPush(app_key, master_secret)
	push = _jpush.create_push()
	push.audience = jpush.audience(jpush.alias(target))
	android_msg = jpush.android(alert=msg, title=title, extras={'username': username})
	push.notification = jpush.notification(alert=msg, android=android_msg)
	push.platform = jpush.all_
	push.send()

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
		#if userinfo:
		try:
			user = User.objects.get(username=target)
			send_msg(username=username, target=target, title="BiuChat", msg=msg)
			# code = 0: OK
			response['code'] = 0
			return HttpResponse(json.dumps(response), content_type="application/json")
		except:
			return HttpResponse(json.dumps(response), content_type="application/json")
		#else:
			# code = 2: 用户未登录
			#response['code'] = 2
			#return HttpResponse(json.dumps(response), content_type="application/json")
	else:
		return HttpResponse("This should be done in a POST method!")

# 返回biu中目标列表
def search_debug(request):
	if request.method == 'POST':
		username = request.POST['username']
		direction = float(request.POST['direction'])
		error_xy = float(request.POST['error_xy'])
		error1 = float(request.POST['error1'])
		error2 = float(request.POST['error2'])
		# code = 1: 用户名不存在
		response = {'code': 1}
		userinfo = request.session.get('onlineuser', None)
		# 验证是否已登录
		#if userinfo:
		try:
			users = User.objects.all();
			user = users.get(username=username)
			user_list = users.exclude(username=username)
			# 换算为平面坐标角度
			direction = (-direction + 360 + 90) % 360
			# 斜率
			k = tan(radians(direction))
			# b = y - kx
			b = user.latitude - k * user.longitude
			biued_list = []
			# 方向直线是垂线或水平线
			if (equal(direction, 90, error_xy) or equal(direction, 270, error_xy) or equal(direction, 0, error_xy) or equal(direction, 360, error_xy) or equal(direction, 180, error_xy)):
				for i in user_list:
					if isbiued_special_debug(direction, user.longitude, user.latitude, i.longitude, i.latitude, error_xy, error1):
						biued_list.append({'nickname': i.username})
						try:
							send_msg(username=username, target=i.username, title="Biu", msg="You are BIUed by " + username + " !")
						except Exception, e:
							print e
			# 其它
			else:
				for i in user_list:
					if isbiued(direction, k, b, user, i, error2):
						biued_list.append({'nickname': i.username})
						try:
							send_msg(username=username, target=i.username, title="Biu", msg="You are BIUed by " + username + " !")
						except Exception, e:
							print e
			response = {'count': len(biued_list)}
			response['users'] = biued_list
			response['code'] = 0
			return HttpResponse(json.dumps(response), content_type="application/json")
		except:
			return HttpResponse(json.dumps(response), content_type="application/json")
		#else:
			# code = 2: 用户未登录
			#response['code'] = 2
			#return HttpResponse(json.dumps(response), content_type="application/json")
	else:
		return HttpResponse("This should be done in a POST method!")