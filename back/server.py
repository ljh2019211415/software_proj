from calendar import month
from cgitb import text
from cmath import pi
# from crypt import methods
from datetime import date, datetime, timedelta
import json

from requests import RequestException
import const
from tabnanny import check
from unittest import result
from urllib import response
from xmlrpc.client import DateTime
from flask import Flask, make_response, request, session, url_for
from flask_cors import CORS
from sqlalchemy import func, true
from backDB import DB, QueuingUser
from dispatcher import Dispatcher, UserStatus
import os

# 实例化数据库
db = DB()
# 初始化数据库
db.init()

# 实例化算法
dispatcher = Dispatcher(db)
app = Flask(__name__)
# r'/*' 是通配符，让本服务器所有的 URL 都允许跨域请求
CORS(app, resources=r'/*')

# 充电桩系统运行时控制
'''开始充电时'''
# 从usrID到orderID的映射
# {usrID:orderID}
usrActiveOrder = {}
# 请求电量
# {orderID:requestVol}
usrRequestVol = {}
# 存储order中的实际充电量
# {orderID:powerUsed}
actualVolUsed = {}
# 存储order中chargeCost
# {orderID:chargeCost}
actualChargeCost = {}


# TODO:检查是否维护了所有的六张表
@app.route("/")
def printAllTestURL():
    urlTestList = '{'
    urlTestList += '\nusrLogon: ' + request.url + url_for('usrLogon', name='Jackie', password='114514')
    urlTestList += '\nusrLogin: ' + request.url + url_for('usrLogin', name='Jackie', password='114514')
    urlTestList += '\nusrResetPWD: ' + request.url + url_for('usrResetPWD', name='Jackie', password='114514')
    urlTestList += '\nusrPersonal: ' + request.url + url_for('usrPersonal', name='Jackie', password='114514')
    urlTestList += '\nusrGetQueueNo: ' + request.url + url_for('usrGetQueueNo', name='Jackie', chargingMode='F')
    urlTestList += '\nadminUsrInfo: ' + request.url + url_for('adminUsrInfo')
    urlTestList += '\n}'
    # print(urlTestList)
    return urlTestList


@app.route("/usr/logon", methods=['POST'])
def usrLogon():
    name = request.json['name']
    password = request.json['password']
    id = db.addUser(name, password)
    return json.dumps({'id': id})


@app.route("/usr/unsubscrib", methods=['POST'])
def usrUnsubscrib():
    name = request.json['name']
    password = request.json['password']
    # checkResult成功时返回id，失败时返回0或-1
    checkResult = db.checkUserPwd(name, password)
    if checkResult > 0:
        db.deleteQueuingUser(name)
        return json.dumps('Your account: ' + str(db.deleteUser(name)) + ' has been delete now.')
    elif checkResult == 0:
        return json.dumps({'status': 'Password Error', 'id': 0})
    else:
        return json.dumps({'status': 'UsrId Not Found', 'id': -1})


@app.route("/usr/login", methods=['POST'])
def usrLogin():
    name = request.json['name']
    password = request.json['password']

    # checkResult成功时返回id，失败时返回0或-1
    checkResult = db.checkUserPwd(name, password)
    if checkResult > 0:
        return json.dumps({'status': 'UsrId OnLine Now', 'id': checkResult})
    elif checkResult == 0:
        return json.dumps({'status': 'Password Error', 'id': 0})
    else:
        return json.dumps({'status': 'UsrId Not Found', 'id': -1})


@app.route("/usr/resetpwd", methods=['POST'])
def usrResetPWD():
    name = request.json['name']
    password = request.json['password']

    # checkResult成功时返回id，失败时返回-1
    checkResult = db.resetUserPwd(name, password)
    return json.dumps({'id': checkResult})


@app.route("/usr/personal", methods=['POST'])
def usrPersonal():
    name = request.json['name']
    password = request.json['password']

    # checkResult成功时返回id，失败时返回-1
    checkResult = db.checkUserPwd(name, password)
    if checkResult > 0:
        return db.getUserInfo(name)
    else:
        return json.dumps({'id': -1, 'status': 'UsrId or UsrName Not Found'})


@app.route("/usr/getqueueno", methods=['POST'])
def usrGetQueueNo():

    usrName = request.json['name']
    chargingMode = request.json['chargingMode']
    requestVol = request.json['requestVol']
    timeOfApplyingNo = datetime.now()

    # FIXME:carStatus判断是否加入等待区
    # FIXME:addCar()需要queueNo，queueNo不包括未加入等待区的车辆
    # print("---0")
    # print(usrName)
    usrInfo = db.getUserInfo(usrName)
    if usrInfo is None:
        # print("---1")
        return json.dumps('The User: ' + str(usrName) + ' didn`t logon.')
    if dispatcher.available() is False:
        return json.dumps('There are not enough spaces in the waiting area!')

    usrID = usrInfo['id']
    # 向数据库中添加排队信息
    usrQueueNo = db.addQueuingUser(usrID, usrName, chargingMode, requestVol, timeOfApplyingNo)
    if usrQueueNo == -1:
        return json.dumps('The chargingMode could not be understood!')
    elif usrQueueNo == -2:
        # print('-2')
        return json.dumps('The user has been in the queue!')
    elif usrQueueNo == 0:
        return json.dumps('The account couldn`t be found!')
    # 向算法中添加排队信息
    dispatcher.addCar(usrQueueNo, usrName, chargingMode, requestVol)
    # print(152, usrName)
    # 获取车辆状态
    carStatus, chargePileID = dispatcher.carStatus(usrName)
    # 获取前序车辆数
    carsAhead = dispatcher.carsAhead(usrName)
    return json.dumps({ 'queueNo' : usrQueueNo,
                        'carStatus' : carStatus,
                        'chargePileID' : chargePileID,
                        'carsAhead' : carsAhead })

@app.route("/usr/cancel", methods=['POST', 'GET'])
def usrCancel():
    usrID = request.json['id']
    usrName = db.getUserInfo(usrID)['name']
    carStatus, chargePileID = dispatcher.carStatus(usrName)
    if carStatus == 3:
        dispatcher.exitCar(usrName)
        return json.dumps({'msg': 'success to cancel!'})
    elif carStatus == 2 or carStatus == 1:
        dispatcher.exitCar(usrName)
        db.deleteQueuingUser(usrName)
        return json.dumps({'msg': 'success to cancel!'})
    elif carStatus == 0:
        return json.dumps({'msg': 'Please visit:' + url_for('usrEndCharging') + 'now!'})


@app.route("/usr/modify-chargingreq", methods=['POST', 'GET'])
def usrModifyChargingReq():
    usrID = request.json['id']
    usrName = db.getUserInfo(usrID)['name']
    carStatus, chargePileID = dispatcher.carStatus(usrName)
    requestVol = request.json['requestVol']
    chargeMode = db.getQueuingUserInfo(usrID)['mode']
    newChargeMode = request.json['chargeMode']

    if carStatus == 2 or carStatus == 3:
        if newChargeMode == chargeMode:
            dispatcher.changeChargePower(usrName, requestVol)
            db.setRequestVol(usrID, requestVol)
            return json.dumps({'requestVol': requestVol})
        else:
            newQueueNo = db.setChargeMode(usrName, newChargeMode)
            db.setRequestVol(usrName, requestVol)
            dispatcher.exitCar(usrName)
            dispatcher.addCar(newQueueNo, usrName, newChargeMode, requestVol)
            carStatus, chargePileID = dispatcher.carStatus(usrName)
            carsAhead = dispatcher.carsAhead(usrName)
            return json.dumps({ 'queueNo' : newQueueNo,
                        'carStatus' : carStatus,
                        'chargePileID' : chargePileID,
                        'carsAhead' : carsAhead })
    elif carStatus == 0 or carStatus == 1:
        return json.dumps(
            {'msg': 'Fail to modify: Forbidden to modify in the charging-area!Please cancel and get a new queueno!'})


@app.route("/usr/car-status", methods=['POST', 'GET'])
def usrStatusPolling():
    usrID = request.json['id']
    usrName = db.getUserInfo(usrID)['name']


    # 获取车辆状态
    carStatus, chargePileID = dispatcher.carStatus(usrName)
    print(int(usrName) - 2, carStatus, chargePileID)
    # 等待中

    if carStatus == 3:
        return json.dumps({'carStatus': carStatus, 'status':'prewaiting', 'carsAhead':dispatcher.carsAhead(usrName), 'chargePileID': chargePileID})
    elif carStatus == 2:
        return json.dumps({'carStatus': carStatus, 'status':'waiting', 'carsAhead':dispatcher.carsAhead(usrName), 'chargePileID': chargePileID})
    elif carStatus == 1:
        return json.dumps({'carStatus': carStatus, 'status':'charging-waiting', 'carsAhead':dispatcher.carsAhead(usrName), 'chargePileID': chargePileID})
    elif carStatus == 0:
        if usrID not in usrActiveOrder.keys():
            return json.dumps({'carStatus': carStatus, 'status':'charging', 'carsAhead': 0, 'chargePileID': chargePileID})

    # 已经开始充电
    orderID = usrActiveOrder[usrID]
    chargeMode = db.getQueuingUserInfo(usrID)['mode']
    # 充电完成
    if actualVolUsed[orderID] >= int(usrRequestVol[orderID]):
        return json.dumps({'status': 'charging-finished', 'carsAhead': 0})
    # 充电中
    # 每1s一次轮询，时间比例1:10
    if chargeMode == 'F':
        incVol = (const.QUICK_CHARGE_POWER) / 60  # 快充电量增值
    elif chargeMode == 'T':
        incVol = (const.SLOW_CHARGE_POWER) / 60  # 慢充电量增值
    actualVolUsed[orderID] += incVol
    actualChargeCost[orderID] += incVol * db.getVolPrice(datetime.now())
    return json.dumps({'carStatus': carStatus, 'status': 'charging', 'incVol': incVol, 'chargePileID': chargePileID, 'usedVol': actualVolUsed[orderID], 'usedCost': actualChargeCost[orderID]})


@app.route("/usr/start-charging", methods=['POST', 'GET'])
def usrStartCharging():
    usrID = request.json['id']
    usrName = db.getUserInfo(usrID)['name']
    requestVol = request.json['requestVol']
    startVol = request.json['startVol']
    carVol = request.json['carVol']
    print(int(usrName) - 2, "start-charging")
    carStatus, chargePileID = dispatcher.carStatus(usrName)
    if carStatus == 3:
        return json.dumps({'msg': 'Request Fail: You are in the preWaitingQueue now!'})
    elif carStatus == 2:
        return json.dumps({'msg': 'Request Fail: You are in the WaitingQueue now!'})
    elif carStatus == 1:
        return json.dumps({'msg': 'Request Fail: You are in the charging-area WaitingQueue now!'})
    else:
        orderID = db.addOrder(usrID, usrName)  # 创建充电详单
        usrActiveOrder[usrID] = orderID  # 添至加运行时控制
        usrRequestVol[orderID] = requestVol  # 记录请求电量
        actualVolUsed[orderID] = 0  # 添加至用电计数
        actualChargeCost[orderID] = 0.0  # 添加至用电计费

        startUpTime=datetime.now()  # 默认使用系统时间作为开始充电时间
        # 测试时前段会传递开始时间
        if 'year' in request.json.keys():
            startUpTime = datetime(year=int(request.json['year']),
                                    month=int(request.json['month']),
                                    day=int(request.json['day']),
                                    hour=int(request.json['hour']),
                                    minute=int(request.json['minute']),
                                    second=int(request.json['second']))

        db.setOrderWhenStartCharging(orderID=orderID,
                                     idOfChargePile=chargePileID,
                                     startUpTime=startUpTime,
                                     startingVol=startVol)  # 初始化详单字段
        db.addServingCarInfo(chargePileID, usrID, carVol)
        return json.dumps({'orderID': orderID})


@app.route("/usr/end-charging", methods=['POST', 'GET'])
def usrEndCharging():
    usrID = request.json['id']
    usrName = db.getUserInfo(usrID)['name']
    print(int(usrName)-2, "end-charging")
    orderID = usrActiveOrder[usrID]  # 获取usrID对应orderID
    # 计算充电时间
    chargingStartTime = db.getOrder(orderID=orderID)['startUpTime']
    chargingStartTime = chargingStartTime.split('.')[0]
    pileID = db.getOrder(orderID=orderID)['idOfChargePile']

    # 默认使用系统时间作为结束时间
    chargingEndTime = datetime.now()
    # 测试时前段会传递结束时间
    if 'year' in request.json.keys():
        chargingEndTime = datetime(year=int(request.json['year']),
                                month=int(request.json['month']),
                                day=int(request.json['day']),
                                hour=int(request.json['hour']),
                                minute=int(request.json['minute']),
                                second=int(request.json['second']))
    t = datetime.strptime(chargingStartTime, '%Y-%m-%d %H:%M:%S')
    chargingTime = (t - chargingEndTime) / timedelta(minutes=1)

    dispatcher.exitCar(usrName)  # 从算法中删除
    db.setOrderWhenStopCharging(orderID = orderID,
                                orderGenerationTime = datetime.now(),
                                actualCharge = actualVolUsed[orderID],
                                chargingTime = chargingTime,
                                stopTime = chargingEndTime,
                                chargingCost = actualChargeCost[orderID],
                                serviceCost = actualVolUsed[orderID] * 0.8
                                )  # 设定结束充电的详单信息

    # 维护报表
    db.setReportTime(pileID=pileID, reportTime=datetime.now())
    db.addTotalUsedTimes(pileID=pileID)
    db.addTotalUsedMinutes(pileID=pileID, timeToAdd=chargingTime)
    db.addTotalUsedVol(pileID=pileID, volToAdd=actualVolUsed[orderID])
    db.addTotalChargeCost(pileID=pileID, costToAdd=actualChargeCost[orderID])
    db.addTotalServiceCost(pileID=pileID, costToAdd=actualVolUsed[orderID] * 0.8)

    # 删除相关表中信息
    # order表不删除相关信息
    usrActiveOrder.pop(usrID)  # 从运行时控制中删除
    usrRequestVol.pop(orderID)  # 从请求电量中删除
    actualVolUsed.pop(orderID)  # 从实际电量中删除
    actualChargeCost.pop(orderID)  # 从电量计费中删除
    # FIXME:充电桩服务车辆信息表似乎会重复主键？
    db.deleteServingCarInfo(pileID, usrID)  # 从充电桩服务车辆信息表（表六）中删除
    db.deleteQueuingUser(usrID)  # 排队表（表一）中删除

    return json.dumps(str(db.getOrder(orderID)))


@app.route("/usr/order-info", methods=['POST', 'GET'])
def usrGetOrderInfo():
    usrID = request.json['id']
    orderID = usrActiveOrder[usrID]
    return '{' + f'''"data": {str(db.getOrder(orderID))}''' + '}'


@app.route("/usr/history-orders", methods=['POST', 'GET'])
def usrGetHistoryOrders():
    usrName = request.json['name']
    return json.dumps({'data':db.getUsrHistoryOrders(usrName)})

@app.route("/admin/usr-info", methods=['POST'])
def adminUsrInfo():
    return '{' + f'''"data": {str(db.getUserInfo())}''' + '}'


@app.route("/admin/queue-info", methods=['POST'])
def adminQueuingUserInfo():
    return '{' + f'''"data": {str(db.getAllQueuingUserInfo())}''' + '}'


@app.route("/admin/charger/status", methods=['POST', 'GET'])
def adminGetChargerStatus():
    reportInfo = db.getAllReportInfo()
    pileInfo = db.getAllPileInfo()
    return '{' + f'''"allReportInfo":  {str(reportInfo)}, "allPileInfo": {str(pileInfo)}''' + '}'


@app.route("/admin/charger/service", methods=['POST', 'GET'])
def adminGetChargerService():
    # 根据充电桩id整合数据
    info = json.loads(str(db.getAllServingCarInfo()))
    startChargingTime = json.loads(str(db.getAllOrderInfo()))  # startUpTime
    getQueueNoTime = json.loads(str(db.getAllQueuingUserInfo()))  # queueTime
    # 测试数据
    # info = [{
    #     'id': '1',
    #     'client_id': '1',
    #     'request_vol': 1,
    #     'car_vol': 1
    #
    # }]
    t = list()
    for a in startChargingTime:
        for b in getQueueNoTime:
            if a['userID'] == b['id']:
                # print(a['startUpTime'] - b['applyTime']) / timedelta(minutes=1)
                temp = dict()
                temp['cost'] = actualChargeCost.get(a['orderID'])
                temp['used_vol'] = actualVolUsed.get(a['orderID'])
                temp['client_id'] = b['id']
                if type(a['startUpTime']) is str:
                    ta = a['startUpTime'].split('.')[0]
                    a['startUpTime'] = datetime.strptime(ta, '%Y-%m-%d %H:%M:%S')
                if type(b['applyTime']) is str:
                    tb = b['applyTime'].split('.')[0]
                    b['applyTime'] = datetime.strptime(tb, '%Y-%m-%d %H:%M:%S')
                temp['queue_minutes'] = (a['startUpTime'] - b['applyTime']) / timedelta(minutes=1)
                t.append(temp)
    for inf in info:
        for temp in t:
            if inf['client_id'] == temp['client_id']:
                inf['queue_minutes'] = temp['queue_minutes']
                inf['cost'] = temp['cost']
                inf['used_vol'] = temp['used_vol']

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

    return json.dumps({'data': items})


@app.route("/admin/charger/statistic", methods=['POST', 'GET'])
def adminGetChargerStatistic():
    return '{' + f'''"data": {str(db.getAllReportInfo())}''' + '}'


@app.route("/admin/charger/open", methods=['POST', 'GET'])
def adminChargeTurnOn():
    chargerID = request.json['chargerID']
    dispatcher.onCharger(chargerID)  # 算法模块中开启charger
    return str(db.turnOnPile(chargerID))


@app.route("/admin/charger/close", methods=['POST', 'GET'])
def adminChargeTurnOff():
    chargerID = request.json['chargerID']
    dispatcher.offCharger(chargerID)  # 算法模块中关闭charger
    return str(db.turnOffPile((chargerID)))


@app.route("/admin/charger/break", methods=['POST', 'GET'])
def adminChargeBreak():
    chargerID = request.json['chargerID']
    dispatcher.offCharger(chargerID)  # 算法模块中关闭charger
    return str(db.setPileBroken(chargerID))


@app.route("/admin/charger/fix", methods=['POST', 'GET'])
def adminChargeFix():
    chargerID = request.json['chargerID']
    dispatcher.onCharger(chargerID)  # 算法模块中开启charger
    return str(db.setPileWork(chargerID))

if __name__ == '__main__':
    print('HelloWorld')
    app.run(port='5000')
