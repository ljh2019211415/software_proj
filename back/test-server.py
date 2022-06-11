from cgi import test
import requests

def testUsrLogon():
    url = 'http://127.0.0.1:5000/usr/logon'
    json = { "name" : '小红' , "password":'114514'}
    res = requests.post(url=url, json=json)
    print(res.json())

def testUsrLogin():
    url = 'http://127.0.0.1:5000/usr/login'
    json = { "name" : '小红' , "password":'114514'}
    res = requests.post(url=url, json=json)
    print(res.json())

def testUsrUnsubscrib():
    url = 'http://127.0.0.1:5000/usr/unsubscrib'
    json = { "name" : '小红' , "password":'114514'}
    res = requests.post(url=url, json=json)
    print(res.json())

def testGetQueueNo():
    url = 'http://127.0.0.1:5000/usr/getqueueno'
    json = { "name" : '小红' , "chargingMode" : 'F', "requestVol" : '11.4514'}
    res = requests.post(url=url, json=json)
    print(res.json())

def testUsrInfo():
    url = 'http://127.0.0.1:5000/admin/usr-info'
    json = { "chargerID" : 1 }
    res = requests.post(url=url, json=json)
    print(res.json())

def testQueuingUsrInfo():
    url = 'http://127.0.0.1:5000/admin/queue-info'
    json = { "chargerID" : 1 }
    res = requests.post(url=url, json=json)
    print(res.json())

def testChargersStatus():
    url = 'http://127.0.0.1:5000/admin/charger/status'
    json = { "chargerID" : 1 }
    res = requests.post(url=url, json=json)
    print(res.json())

def testChargersService():
    url = 'http://127.0.0.1:5000/admin/charger/service'
    json = { "chargerID" : 1 }
    res = requests.post(url=url, json=json)
    print(res.json())

def testChargersStatistic():
    url = 'http://127.0.0.1:5000/admin/charger/statistic'
    json = { "chargerID" : 1 }
    res = requests.post(url=url, json=json)
    print(res.json())

def testChargerTurnOn():
    url = 'http://127.0.0.1:5000/admin/charger/open'
    json = { "chargerID" : 1 }
    res = requests.post(url=url, json=json)
    print(res.json())

def testChargerTurnOff():
    url = 'http://127.0.0.1:5000/admin/charger/close'
    json = { "chargerID" : 1 }
    res = requests.post(url=url, json=json)
    print(res.json())

def testChargeBreak():
    url = 'http://127.0.0.1:5000/admin/charger/break'
    json = { "chargerID" : 1 }
    res = requests.post(url=url, json=json)
    print(res.json())

def testChargeFix():
    url = 'http://127.0.0.1:5000/admin/charger/fix'
    json = { "chargerID" : 1 }
    res = requests.post(url=url, json=json)
    print(res.json())

testUsrLogon()
testUsrLogin()
testGetQueueNo()
# testQueuingUsrInfo()
testUsrUnsubscrib()
# testUsrInfo()
# testChargersStatus()
# testChargersService()
# testChargersStatistic()
# testChargerTurnOn()
# testChargerTurnOff()
# testChargeBreak()
# testChargeFix()