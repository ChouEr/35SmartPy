import sys
import time
import thread
import math
sys.path.append("../libs")
from proContext import *
from proMCU import *
from proUTM import *
import UTM

global speed_set
global speed_back
global speed_mode
global output
global speed_way
global canSpeed
global canSteer
global planSteer

output = 0

def main():

    global canSpeed
    global canSteer
    global planSteer
    ctx = proContext()

    pub = ctx.socket(zmq.PUB)
    pub.bind('tcp://*:8080')

    pubCAN = ctx.socket(zmq.PUB)
    pubCAN.bind('tcp://*:8088')

    mcu = MCU()

    canSpeed = 0
    uartSpeed = 0
    canSteer = 0

    lastCmd = 0
    lastSteer = 0
    control = True

    def readGNSS():
        global canSpeed
        global canSteer
        i = 0
        while True:
            mcu.readGNSS()
            uartSpeed = math.sqrt (mcu.gnssRead.v_n ** 2 + mcu.gnssRead.v_e ** 2 + mcu.gnssRead.v_earth ** 2 )
            content = {"Length":mcu.gnssRead.length,"Mode":mcu.gnssRead.mode,"Time1":mcu.gnssRead.time1,"Time2":mcu.gnssRead.time2, \
                       "Num":mcu.gnssRead.num,"Lat":mcu.gnssRead.lat,"Lon":mcu.gnssRead.lon,"Height":mcu.gnssRead.height, \
                       "V_n":mcu.gnssRead.v_n,"V_e":mcu.gnssRead.v_e,"V_earth":mcu.gnssRead.v_earth, \
                       "Roll":mcu.gnssRead.roll,"Pitch":mcu.gnssRead.pitch,"Head":mcu.gnssRead.head, \
                       "A_n":mcu.gnssRead.a_n,"A_e":mcu.gnssRead.a_e,"A_earth":mcu.gnssRead.a_earth, \
                       "V_roll":mcu.gnssRead.v_roll,"V_pitch":mcu.gnssRead.v_pitch,"V_head":mcu.gnssRead.v_head, \
                       "Status":mcu.gnssRead.status}
            i = (i+1) % 9999
            if i%20 ==0:
                print(content)
                print('***************')
                print('*************************************')
            pub.sendPro('CurGNSS',content)
        pass

    def readCAN():
        global canSpeed
        global canSteer
        i = 0
        while True:
            time.sleep(0.05)
            mcu.readBrake()
            content = {'Time':mcu.brakeRead.Time, 'Button':mcu.brakeRead.Button, 'Remoter':mcu.brakeRead.Remoter,\
                       'Pedal':mcu.brakeRead.Pedal, 'Can':mcu.brakeRead.Pedal, 'RemoterS':mcu.brakeRead.RemoterS, \
                       'Real':mcu.brakeRead.Real}
            pubCAN.sendPro('CANBrake',content)
            i = (i + 1)% 9999
            if i % 25 == 0:
                #print(content)
                pass

            mcu.readGun()
            content = {'Mode':mcu.gunRead.Mode, 'Depth':mcu.gunRead.Depth, 'Speed':mcu.gunRead.Speed}
            canSpeed = mcu.gunRead.Speed
            #print('canSpeed',canSpeed)
            #print('**********************************************************')
            pubCAN.sendPro('CANGun',content)

            mcu.readSteer()
            content = {'Mode':mcu.steerRead.Mode, 'Torque':mcu.steerRead.Torque, 'EException':mcu.steerRead.EException, \
                       'AngleH':mcu.steerRead.AngleH, 'AngleL':mcu.steerRead.AngleL, 'Calib':mcu.steerRead.Calib, \
                       'By6':mcu.steerRead.By6, 'Check':mcu.steerRead.Check}
            canSteer = mcu.steerRead.AngleH * 256 + mcu.steerRead.AngleL - 1024
            #print('---------------------------------',canSteer)
            pubCAN.sendPro('CANSteer',content)
        pass

    def alpha(v):
        return 100/ (v**2)

    def sendCmd(content):
        global planSteer
        if content['Who'] == 'Brake':
            mcu.brakeSend.Mode = content['Mode']
            mcu.brakeSend.Depth = content['Value']
            mcu.sendBrake()
            pass
        elif content['Who'] == 'Gun': 
            mcu.gunSend.Mode = content['Mode']
            mcu.gunSend.Depth = content['Value']
            speed = min(canSpeed/3.6, uartSpeed)
            if speed > 0 and math.fabs(steer) > alpha(speed):
                mcu.gunSend.Depth = 0x00
            mcu.sendGun()
            pass
        elif content['Who'] == 'Steer':
            speed = min(canSpeed/3.6, uartSpeed)
            steer = content['Value']
            #if speed > 0:
            #    steer = min( steer, alpha(speed) )
            gap  = 0
            if canSpeed > 25:
                gap = 1000.0 / ( (canSpeed/3.6) ** 2 )
            if canSpeed > 25 and steer < planSteer - gap:
                steer = planSteer - gap
            if canSpeed > 25 and steer > planSteer + gap:
                steer = planSteer + gap
            planSteer =  steer
            #print('send steer is : ',steer)
            mcu.steerSend.Mode = content['Mode']
            mcu.steerSend.AngleH =  int( (steer + 1024)/256)
            mcu.steerSend.AngleL =  int ( (steer + 1024) % 256)
            mcu.sendSteer()
            pass
        pass

    def recvControl():
        subCAN = ctx.socket(zmq.SUB)
        subCAN.connect('tcp://localhost:8082')
        subCAN.setsockopt(zmq.SUBSCRIBE,'Cmd')
        while True:
            lastCmd = time.time()
            content = subCAN.recvPro()
            #print(content)
            sendCmd(content)
        pass

    def recvSteer():
        lastSteer = time.time()
        subSteer = ctx.socket(zmq.SUB)
        subSteer.connect('tcp://localhost:8081')
        subSteer.setsockopt(zmq.SUBSCRIBE,'PlanSteer')
        i = 0
        while True:
            content = subSteer.recvPro()
            content = {'Who':'Steer','Mode':content['Mode'],'Value':content['Value']}
            i = (i + 1)% 9999
            if i % 25 == 0:
                pass
                #print(content)
            sendCmd(content)
        pass
        
    thread.start_new_thread(readGNSS, ())
    thread.start_new_thread(readCAN, ())
    thread.start_new_thread(recvControl, ())
    thread.start_new_thread(recvSteer, ())

    i = 0
    while True:
        if time.time() - lastSteer > 2:
        #    content = {'Who':'Steer','Mode':0x10,'Value':0x00}
        #    sendCmd(content)
        #    content = {'Who':'Brake','Mode':0x01,'Value':0x9f}
        #    sendCmd(content)
        #    content = {'Who':'Gun','Mode':0x00,'Value':0x00}
        #    sendCmd(content)
            pass
        if time.time() - lastCmd > 2:
            pass
        i = (i+1) % 9999
        time.sleep(1)

if __name__ == "__main__":
    main()
