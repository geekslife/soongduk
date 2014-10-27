#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mechanize import Browser
from bs4 import BeautifulSoup
import urllib2
import os.path
import sys, json
from mailer import Mailer, Message

BASE_URL = 'http://www.soongduck.es.kr'
HOME_URL = "%s/index/index.do"%BASE_URL
BBS_URL = "%s/notice/board.do?bcfNo=1216205"%BASE_URL

conf = json.loads(open('conf.json').read())

USERNAME = conf['sd_id']
PASSWORD = conf['sd_pw']
MAILER_USERNAME = conf['gg_id']
MAILER_PASSWORD = conf['gg_pw']
MAILER_TO = conf['gg_to']

browser = Browser()
browser.set_handle_robots(False)

class LastItemInfo:
    filename = 'last-item-num.txt'
    @staticmethod
    def setNum(num):
        open(LastItemInfo.filename,'w').write(num)

    def __init__(self):
        if not os.path.isfile(self.filename) :
            open(self.filename,'w').write('0')
        self.lastnum = open(self.filename).read()

    def getNum(self):
        return self.lastnum

def removeHwp():
    import glob
    import os
    for hwp in glob.glob("*.hwp"):
        os.remove(hwp)

def login():
    ''' returns html '''
    browser.open(HOME_URL)
    #browser.select_form(nr=0)
    browser.select_form('wgt_login_form')
    browser.form['userid'] = USERNAME
    browser.form['userpasswd'] = PASSWORD
    browser.submit()
    #return urlopen( BBS_URL ).read()

def parseItems():
    ''' returns notice items '''
    soup = BeautifulSoup(browser.open(BBS_URL))
    lastnum = LastItemInfo().getNum()
    items = []

    for tr in soup.find_all('tr', attrs={'class':'bg1'}):
        num = tr.find('td',attrs={"num"})
        if num.text == lastnum : # stop if old item
            break
        it = {}
        it['num'] = num.text
        it['title'] = tr.find('td',attrs={'title'}).text.strip()
        it['link'] = tr.find('a')['href']
        items.append(it)
    return items

def fetchHwp(item):
    ''' returns itemnum.hwp or  None '''
    filename = None
    itemUrl = "%s/notice/%s"%(BASE_URL,item['link'])
    html = browser.open(itemUrl).read()
    soup = BeautifulSoup(html)
    attach_file = soup.find('dl',attrs={'class':'attach_file'})
    if attach_file:
        attachFileUrl = BASE_URL + attach_file.find('a')['href']
        data = browser.open(attachFileUrl).read()
        filename = "%s.hwp"%item['num']
        open(filename,'wb').write(data)
    return filename

def sendMail(item, hwp):
    sender = Mailer('smtp.gmail.com',use_tls=True)
    for to in MAILER_TO :
        sender.login(MAILER_USERNAME,MAILER_PASSWORD)
        message = Message(From='valley.cloulu@gmail.com', To=to)
        message.Subject = "가정통신문 :%s"%item['title'].encode('utf-8')
        message.Html = ""
        if hwp:
            message.attach(hwp)
        sender.send(message)

if __name__ == '__main__':
    removeHwp()
    login()
    items = parseItems()
    if not items:
        sys.exit(0)

    LastItemInfo.setNum(items[0]['num'])
    for it in items:
        print it['title'].encode('utf-8'), it['link']
        hwp = fetchHwp(it)
        sendMail(it, hwp)
