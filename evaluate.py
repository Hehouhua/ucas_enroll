#!/usr/bin/env python
# -* - coding: UTF-8 -* -
##
# @file evaluate.py
# @brief 
# @author scusjs@foxmail.com
# @version 0.1.00
# @date 2015-12-19

#
# @modify by hehe077	
# @date:2016-09-01
# @	适修改功能的web接口
# @ 添加退课功能
# @ 增加学位课和非学位课切换的功能 （慎用）
#

import requests
import ConfigParser
from bs4 import BeautifulSoup
import re
import threading
import time
import sys
reload(sys)
sys.setdefaultencoding('utf8')

class UCASEvaluate(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.__readCoursesId()
		self.enrollCount = {}
		cf= ConfigParser.RawConfigParser()
		cf.read('config')
		self.username=cf.get('info', 'username')
		self.password=cf.get('info', 'password')
		self.loginUrl="http://sep.ucas.ac.cn/slogin"#login ok
		self.enroll = cf.getboolean('action', 'enroll')
		self.evaluate = cf.getboolean('action', 'evaluate')
		self.loginPage="http://sep.ucas.ac.cn"
		self.courseSelectionPage="http://sep.ucas.ac.cn/portal/site/226/821"#进入选课系统
		#self.studentCourseSelectionSystem="http://jwjz.ucas.ac.cn/Student/"
		self.studentCourseIndentify="http://jwxk.ucas.ac.cn/login?Identity="
		self.studentCourseTop="http://jwxk.ucas.ac.cn/courseManage/main"
		self.studentCourseEvaluateUrl="http://jwjz.ucas.ac.cn/Student/DeskTopModules/"
		self.selectCourseUrl = "http://jwxk.ucas.ac.cn/courseManage/selectCourse"
		self.saveCourseUrl = "http://jwxk.ucas.ac.cn/courseManage/saveCourse"
		self.delCourseUrl="http://jwxk.ucas.ac.cn/courseManage/del/"
		self.dict={"01":"910",
				"02":"911",
				"03":"957",
				"04":"912",
				"05":"928",
				"06":"913",
				"07":"914",
				"08":"921",
				"09":"951",
				"10":"952",
				"11":"958",
				"12":"917",
				"13":"945",
				"14":"927",
				"15":"915",
				"16":"954",
				"17":"955",
				"18":"959",
				"TY":"946",
				"19":"961",
				"20":"963",
				"21":"962"
		}
		self.timeout=5
		self.headers = {
				#'Host': 'sep.ucas.ac.cn',为什么有的host自动更新，有的就没有？
				'Connection': 'keep-alive',
				'Pragma': 'no-cache',
				'Cache-Control': 'no-cache',
				'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
				'Upgrade-Insecure-Requests': '1',
				'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36',
				'Accept-Encoding': 'gzip, deflate, sdch',
				'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',

		}
		self.s = requests.Session()
		loginPage = self.s.get(self.loginPage, headers=self.headers,timeout=self.timeout)#http://sep.ucas.ac.cn
		self.cookies = loginPage.cookies
		self.courseId = open("courseid", "r").read().splitlines();

	def login(self):
		postdata = {
			'userName' : self.username,
			'pwd' : self.password,
			'sb'	   : 'sb'
		}
		response = self.s.post(self.loginUrl, data=postdata, headers=self.headers,timeout=self.timeout)#http://sep.ucas.ac.cn/slogin
		#print response.text
		if self.s.cookies.get_dict().has_key('sepuser'):
			return True
		return False
	
	def __readCoursesId(self):
		coursesFile = open('./courseid', 'r')
		self.coursesId = {}
		for line in coursesFile.readlines():
			line = line.strip().split('//')[0].strip().split(':')
			courseId = line[0]
			self.coursesId[courseId]={}
			isDegree = False
			if len(line) == 2 and line[1] == "on":
				isDegree = True
			self.coursesId[courseId]['isDegree'] = isDegree
			
	def delCourse(self,courseId,sids):
		delCourseUrl=self.delCourseUrl+sids+"?s="+ self.urlSession
		response = self.s.get(delCourseUrl, headers=self.headers,timeout=self.timeout)
		soup = BeautifulSoup(response.text,"html.parser")
		if "删除成功" in response.text:
			print soup.find(attrs={"id":"loginSuccess"}).get_text()
			self.coursesId[courseId]['alreadyDegree'] = self.coursesId[courseId]['isDegree']
			return True
		else :
			print "Msg: ",courseId," ",soup.find(attrs={"id":"loginSuccess"}).get_text()
			print soup.find(attrs={"id":"loginError"}).get_text()
			return False
			
	def enrollCourses(self):
		response = self.s.get(self.courseSelectionPage, headers=self.headers,timeout=self.timeout)#http://sep.ucas.ac.cn/portal/site/226/821
		soup = BeautifulSoup(response.text,"html.parser")
		#print(response.text.encode('utf8'))
		try:
			indentity = str(soup.noscript).split('Identity=')[1].split('"'[0])[0]
			coursePage = self.studentCourseIndentify + indentity#http://jwxk.ucas.ac.cn/login?Identity=
			response = self.s.get(coursePage,timeout=self.timeout)
			response = self.s.get(self.studentCourseTop,timeout=self.timeout)#可以查看到选上的课
			#print response.text
			#action="/courseManage/selectCourse?s=505540ff-d5ca-4fba-a22f-048e8bbb07c4"
			soup = BeautifulSoup(response.text,"html.parser")
			self.urlSession = str(soup.find_all("form")[0]['action']).strip().split('=')[1]
			all_selected = soup.body.table.tbody.find_all('tr')
			print "urlSession: ",self.urlSession
			coursesId = self.coursesId.copy()
			
			while len(coursesId) > 0:
				for eachCourse in coursesId.keys():
					try:
						if eachCourse in response.text:
							for selected in all_selected:
								if eachCourse in selected.text:
								#<td><a href="/course/courseplan/125724" target="_blank">091M4001H</a></td>
									href=selected.find(attrs={"target":"_blank"})['href']
									self.coursesId[eachCourse]['sids'] = href.split('/')[-1]
									if "是" in selected.text:
										isDegree=True
										self.coursesId[eachCourse]['alreadyDegree']=isDegree
										#print "%s 是学位课 " %eachCourse
									elif "否" in selected.text:
										isDegree=False
										self.coursesId[eachCourse]['alreadyDegree']=isDegree
										#print "%s 是非学位课" %eachCourse
									else:
										print "Maybe Encoding Error,Please check."
										return
									if self.coursesId[eachCourse]['isDegree']==isDegree:
										print("course " + eachCourse + " is in your coursetable")
										del coursesId[eachCourse]
										raise 
					except:
						continue
					if self.enrollCount.has_key(eachCourse):
						self.enrollCount[eachCourse] += 1
					else:
						self.enrollCount[eachCourse] = 1
					try:
						result = self.__enrollCourse(self.urlSession, eachCourse, self.coursesId[eachCourse]['isDegree'], self.enrollCount[eachCourse])
						if result:
							del coursesId[eachCourse]
					except Exception as e:
						print 'Error: ',e
						pass
		except Exception as e:
			print("system error")
			print e
			#self.enrollCourses()
			pass
		except KeyboardInterrupt:
			print("Bye")
	


	def __enrollCourse(self, urlSession, courseId, isDegree, count):
		#self.s.headers.update({'Host': 'jwxk.ucas.ac.cn'})  
		selectCourseUrl = self.selectCourseUrl + "?s=" + urlSession
		saveCourseUrl = self.saveCourseUrl + "?s=" + urlSession
		if self.coursesId[courseId].has_key('alreadyDegree'):#转换学位课非学位课，需要先退课
			if self.coursesId[courseId]['alreadyDegree'] != self.coursesId[courseId]['isDegree']:
				print courseId,"to change degree"
				if self.coursesId[courseId].has_key('sids'):
					self.delCourse(courseId,self.coursesId[courseId]['sids'])
		if self.coursesId[courseId].has_key('courseName') and self.coursesId[courseId].has_key('sids'):
			courseName=self.coursesId[courseId]['courseName']
			code=self.coursesId[courseId]['sids']
			postData={}
			postData['deptIds']=self.dict[courseId[:2]]
			postData['sids'] = code
			if isDegree:#did_125739=125739
				postData["did_"+code] = code
			print("select " + courseName + "   " + str(count) + " times")
		else:
			postData={}
			postData['deptIds']=self.dict[courseId[:2]]
			postData['sb']=0
			response = self.s.post(selectCourseUrl,postData,timeout=self.timeout)#查看还可选的课
			soup = BeautifulSoup(response.text,"html.parser")
			dataTable = soup.body.form.table.tbody.find_all('tr')
			#print (str)(dataTable)
			courseName = "存放当前需要选择的课程"
			for course in dataTable:
				if courseId in course.text:
					code = course.find(attrs={"name":"sids"})['value']
					degreeCheckBoxName = course.find(id=re.compile('did_'+code))['name']
					courseName = course.find_all('a')[1].string
					
					self.coursesId[courseId]['sids']=code
					self.coursesId[courseId]['courseName']=courseName
					postData={}
					postData['deptIds']=self.dict[courseId[:2]]
					postData['sids'] = code
					if isDegree:#did_125739=125739
						postData["did_"+code] = code
					print("select " + courseName + "   " + str(count) + " times")
	
		if 	postData.has_key('sb') :
			print "no such course:" ,courseId
			#print (str)(dataTable)
			#return True
		
		response = self.s.post(saveCourseUrl, data = postData,timeout=self.timeout)
		soup = BeautifulSoup(response.text,"html.parser")
		
		if "选课成功" in response.text:
			print soup.find(attrs={"id":"loginSuccess"}).get_text()
			return True
		elif "选课失败" in response.text:
			print soup.find(attrs={"id":"loginError"}).get_text()
			return False
		elif "时间冲突" in response.text:
			print soup.find(attrs={"id":"loginError"}).get_text()
			return False
		else :#<label id="loginSuccess" class="success"></label>
			#print "Msg: ",courseId
			print "Msg: ",courseId," ",soup.find(attrs={"id":"loginSuccess"}).get_text()
			print soup.find(attrs={"id":"loginError"}).get_text()

	def run(self):
		#ucasEvaluate = UCASEvaluate()
		if not self.login():
			print('login error, please check your username and password')
			exit()
		print('login success')
		if self.enroll:
			print('Enrolling course...\n')
			self.enrollCourses()
		if self.evaluate:
			print('Not Implemented yet...\n')

if __name__=="__main__":
	for i in range(0,2):
		my_thread = UCASEvaluate()  
		my_thread.start()
		print "----------Thread " ,i ," starts----------------- "
		time.sleep(5)


