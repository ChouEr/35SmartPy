#!/usr/bin/env python
import sys 
import time,math,thread,copy

sys.path.append("../libs")
from proContext import *
from proPID import *
import UTM 
import math
import random

def main():
    ctx = proContext()
    pub = ctx.socket(zmq.PUB)
    pub.bind('tcp://*:8081')

    subMap = ctx.socket(zmq.SUB)
    subMap.connect('tcp://localhost:8083')
    subMap.setsockopt(zmq.SUBSCRIBE,'Diff')

    pidDis = PID(P= 10.8, I = 0.0, D = 0.0)
    pidDis.setWindup(50.0)
    pidHead = PID(P= 4.2, I = 0.0, D = 0.0)
    #pidHead = PID(P= 0.0, I = 0.0, D = 0.0)
    pidHead.setWindup(50.0)
    pidDHead = PID(P=4.6, I = 0.0, D = 0.0)
    #pidDHead = PID(P=0.0, I = 0.0, D = 0.0)
    pidDHead.setWindup(25.0)

    

    def recvMap():
        j = 0
        while True:
            content = subMap.recvPro()
            pidDis.SetPoint = 0.0
            pidDis.update(content['Dis'])
            outDis = pidDis.output * -1

            pidHead.SetPoint = 0
            pidHead.update(content['Head'])
            outHead = pidHead.output * -1

            pidDHead.SetPoint = 0
            pidDHead.update(content['DHead'])
            outDHead = pidHead.output * -1

            steer = outDis + outHead + outDHead
            #if outDis < -50:
            #    steer = outDis + outHead
            #steer = outHead + outDHead
            #steer = outDis + outHead 
            #steer = outDis
            #steer = outHead
            #steer = outDHead
            speed = math.fabs(10 * math.cos( math.radians(content['DHead'])*5 ) )

            #content = {'Mode':0x20,'Value':int(steer - 16 + random.randint(0,1) )   }
            #content = {'Mode':0x20,'Value':int(steer - 15)  }
            content = {'Mode':0x20,'Value':int(steer - 14)  }
            pub.sendPro('PlanSteer',content)
            j = (j + 1) % 999999
            if j % 2 == 0:
                print('PlanSteer--->', int(steer) )
                print('.......................................................')
            content = {'Mode':0x00,'Value':speed,'Gear':0}
            #pub.sendPro('PlanSpeed',content)
            pass
    pass
    recvMap()

if __name__ == '__main__':
    main()
    pass

