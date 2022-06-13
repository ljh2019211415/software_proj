from cgitb import text
from cmath import pi
# from crypt import methods
from datetime import datetime
import json
from tabnanny import check
from unittest import result
from urllib import response
from xmlrpc.client import DateTime
from flask import Flask, make_response, request, session, url_for
from flask_cors import CORS
from sqlalchemy import func, true
from backDB import DB, QueuingUser

db = DB()
db.init()
app = Flask(__name__)
# r'/*' 是通配符，让本服务器所有的 URL 都允许跨域请求
CORS(app, resources=r'/*')

@app.route("/")
def printAllTestURL():
    urlTestList = '{'
    urlTestList += '\nusrLogon: ' + request.url + url_for('usrLogon',name='Jackie',password='114514')
    urlTestList += '\nusrLogin: ' + request.url + url_for('usrLogin',name='Jackie',password='114514')
    urlTestList += '\nusrResetPWD: ' + request.url + url_for('usrResetPWD',name='Jackie',password='114514')
    urlTestList += '\nusrPersonal: ' + request.url + url_for('usrPersonal',name='Jackie',password='114514')
    urlTestList += '\nusrGetQueueNo: ' + request.url + url_for('usrGetQueueNo',name='Jackie',chargingMode='F')
    urlTestList += '\nadminUsrInfo: ' + request.url + url_for('adminUsrInfo')
    urlTestList += '\n}'
    print(urlTestList)
    return urlTestList

@app.route("/usr/logon", methods=['POST'])
def usrLogon():
    name = request.json['name']
    password = request.json['password']
    id = db.addUser(name,password)
    return json.dumps({'id':id})

@app.route("/usr/unsubscrib", methods=['POST'])
def usrUnsubscrib():
    name = request.json['name']
    password = request.json['password']
    # checkResult成功时返回id，失败时返回0或-1
    checkResult = db.checkUserPwd(name, password)
    if checkResult > 0:
        db.deleteQueuingUser(name)
        return json.dumps('Your account: '+ str(db.deleteUser(name)) +' has been delete now.')
    elif checkResult == 0:
        return json.dumps({'status':'Password Error', 'id':0})
    else:
        return json.dumps({'status':'UsrId Not Found','id':-1})

@app.route("/usr/login", methods=['POST'])
def usrLogin():
    name = request.json['name']
    password = request.json['password']

    # checkResult成功时返回id，失败时返回0或-1
    checkResult = db.checkUserPwd(name, password)
    if checkResult > 0:
        return json.dumps({'status': 'UsrId OnLine Now', 'id':checkResult})
    elif checkResult == 0:
        return json.dumps({'status': 'Password Error', 'id':0})
    else:
        return json.dumps({'status': 'UsrId Not Found', 'id':-1})

# TODO:是否有必要增加一个在线列表？
@app.route("/usr/resetpwd", methods=['POST'])
def usrResetPWD():
    name = request.json['name']
    password = request.json['password']

    # checkResult成功时返回id，失败时返回-1
    checkResult = db.resetUserPwd(name, password)
    return json.dumps({'id':checkResult})

@app.route("/usr/personal", methods=['POST'])
def usrPersonal():
    name = request.json['name']
    password = request.json['password']

    # checkResult成功时返回id，失败时返回-1
    checkResult = db.checkUserPwd(name, password)
    if checkResult > 0:
        return db.getUserInfo(name)
    else:
        return json.dumps({'id':-1,'status':'UsrId or UsrName Not Found'})

@app.route("/usr/getqueueno", methods=['POST'])
def usrGetQueueNo():
    usrName = request.json['name']
    chargingMode = request.json['chargingMode']
    requestVol = request.json['requestVol']
    timeOfApplyingNo = datetime.now()
    usrInfo = db.getUserInfo(usrName)
    if usrInfo is None:
        return json.dumps('The User: ' + str(usrName) + ' didn`t logon.')
    usrID = usrInfo['id']
    usrQueueNo = db.addQueuingUser(usrID, usrName, chargingMode, requestVol, timeOfApplyingNo)
    return json.dumps({'queueNo' : usrQueueNo})

@app.route("/admin/usr-info", methods=['POST'])
def adminUsrInfo():
    return json.dumps(str(db.getAllUserInfo()))

@app.route("/admin/queue-info", methods=['POST'])
def adminQueuingUserInfo():
    return json.dumps(str(db.getAllQueuingUserInfo()))

# TODO: 获取ReportInfo中的used_times used_minutes used_vol并在此合并返回
@app.route("/admin/charger/status", methods=['POST', 'GET'])
def adminGetChargerStatus():
    reportInfo = db.getAllReportInfo()
    pileInfo = db.getAllPileInfo()
    return json.dumps({'allReportInfo': str(reportInfo), 'allPileInfo': str(pileInfo)})


@app.route("/admin/charger/service", methods=['POST', 'GET'])
def adminGetChargerService():
    # 根据充电桩id整合数据
    info = json.loads(str(db.getAllServingCarInfo()))
    # 测试数据
    # info = [{
    #     'id': '1',
    #     'client_id': '1',
    #     'request_vol': 1,
    #     'car_vol': 1
    #
    # }]
    ids = set()
    # 找到所有id
    for each in info:
        ids.add(each['id'])
    # 整合数据
    items = list()
    for each in ids:
        item = dict()
        item['id'] = each
        item['in_service'] = list()
        for i in info:
            if i['id'] == each:
                item['in_service'].append(i)
        items.append(item)
    return json.dumps(dict({'data': items}))

@app.route("/admin/charger/statistic", methods=['POST', 'GET'])
def adminGetChargerStatistic():
    return json.dumps(str(db.getAllReportInfo()))

@app.route("/admin/charger/open", methods=['POST', 'GET'])
def adminChargeTurnOn():
    chargerID = request.json['chargerID']
    return str(db.turnOnPile(chargerID))

@app.route("/admin/charger/close", methods=['POST', 'GET'])
def adminChargeTurnOff():
    chargerID = request.json['chargerID']
    return str(db.turnOffPile((chargerID)))

@app.route("/admin/charger/break", methods=['POST', 'GET'])
def adminChargeBreak():
    chargerID = request.json['chargerID']
    return str(db.setPileBroken(chargerID))

@app.route("/admin/charger/fix", methods=['POST', 'GET'])
def adminChargeFix():
    chargerID = request.json['chargerID']
    return str(db.setPileWork(chargerID))

if __name__ == '__main__':
    app.run(port='5000')
    print('HelloWorld')