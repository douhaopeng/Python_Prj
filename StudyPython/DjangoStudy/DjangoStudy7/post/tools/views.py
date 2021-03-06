#coding=utf-8
from django.http import HttpResponse
from django.shortcuts import render
import requests
from bs4 import BeautifulSoup
import re
import hashlib
import json
import time

Login_URL   = 'http://210.30.1.112:8089/Self/LoginAction.action'
Random_URL  = 'http://210.30.1.112:8089/Self/RandomCodeAction.action'
GetFlow_URL = 'http://210.30.1.112:8089/Self/nav_getUserInfo'
MainPage_URL= 'http://210.30.1.112:8089/Self/nav_main'
AcStatus_URL= 'http://210.30.1.112:8089/Self/refreshaccount?t=0.521180426934734'
Overdate_URL= 'http://210.30.1.112:8089/Self/MonthPayAction.action'

def index(request):
    return render(request, 'index.html')
     
def add(request):
    a = request.GET['a']
    b = request.GET['b']
    User = Drcom(a,b)
    if(User.login()):
            User.GetFlow()
            User.GetAcStatus()
            User.GetOverData()
	    strr = User.PrintStatus()
    else:
	    strr = u'密码错误'
    return HttpResponse(strr)


class Drcom():
    def __init__(self, username, password):
        self.s = requests.Session()
        self.Username = username
        self.Password = hashlib.md5(password).hexdigest()
        self.Send_Headers = {
                    'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1',
                    'Accept': 'application/x-www-form-urlencoded',
                    'Accept-Language': 'zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3',
                    'Accept-Encoding':    'gzip, deflate',
                    'Referer':    'http://zhjw.dlnu.edu.cn/gradeLnAllAction.do?type=ln&oper=fa'
        }

    def login(self):
        req = self.s.get(Login_URL, timeout = 5)
        self.s.get(Random_URL)
        checkcode = re.findall('var checkcode="(\d*)', req.text, re.S)
        self.postdata = {'account': self.Username,
                'password':self.Password,
                'code':'',
                'checkcode':checkcode[0],
                'Submit':'%E7%99%BB+%E5%BD%95'
        }
        sRes = self.s.post(url=Login_URL,data=self.postdata,timeout=5)
        if u'温馨提示' in sRes.text:
            return True
        else:
            return False

    def GetFlow(self):
        req = self.s.get(GetFlow_URL)
        text = req.text
        soup = BeautifulSoup(text, "lxml")
        tag = soup.find('td', text = re.compile(u"本月流量"))
        tag = tag.find_next_sibling('td')
        sRes = re.findall('(\d+).\d',tag.string)
        self.AcFlowUsed = float(sRes[0]) / 1000.0  #转换单位M->G

    def GetAcStatus(self):
        req = self.s.get(AcStatus_URL)
        GetData = json.loads(req.text)
        AcStatus = GetData['note']
        self.AcUsername     =   AcStatus['welcome']
        self.AcLeftMoeny    =   AcStatus['leftmoeny']
        self.AcService      =   AcStatus['service']
        self.AcOnlineStatus =   AcStatus['onlinestate']
        sGetFlowLimit = re.findall('(\d+)G',AcStatus['service'])      #提取套餐流量限制
        self.AcFlowLimit = float(sGetFlowLimit[0])

    def GetOverData(self):
        req = self.s.post(Overdate_URL, data = {'type': '1' ,'year': time.gmtime()[0]})
        soup = BeautifulSoup(req.text, "lxml")
        try:
            soup = soup.find('tbody').find('td').find_next_sibling('td')
            self.AcOverData = str(soup.string)
        except AttributeError:  # if the date was Null
            self.AcOverData = u'不详'

    def PrintStatus(self):
        self.strr = "************************\n" + self.AcUsername + '\n'
        if self.AcOnlineStatus == 1:
            self.strr = self.strr + u"!-在线-!"
        else:
            self.strr = self.strr + u"--离线--"

        self.strr = self.strr + u"已使用流量：" + str(self.AcFlowUsed) + u"G"
        self.strr = self.strr + u"剩余流量：  " + str(self.AcFlowLimit - self.AcFlowUsed) + u"G"
        self.strr = self.strr + u"到期时间：  " + self.AcOverData
        self.strr = self.strr + self.AcService
        self.strr = self.strr + u"账户余额：" + self.AcLeftMoeny
        self.strr = self.strr + "************************\n"
	return self.strr

