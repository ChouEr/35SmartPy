﻿#!/usr/bin/env python
import sys
import time,math,thread,copy

sys.path.append("../libs")
from proContext import *
import UTM
#convert string to dict
import yaml
#draw something
#import pygame, sys
#from pygame.locals import *

global node
node = {'Lat':0,'Lon':0,'Head':0,'Status':0,'V_e':0,'V_n':0,'V_earth':0}
def main():
    global node
    hdMap = []
    ctx = proContext()
    pub = ctx.socket(zmq.PUB)
    pub.bind('tcp://*:8083')
    def loadmap():
        print('loading map............')
        fi =  open('map.txt','r')
        i = 0
        lastE = 0
        lastN = 0
        for line in fi.readlines():
            i = (i + 1) % 99999
            args = line.split('\t')
            print(args[1])
            E,N,Z,Z_l = UTM.from_latlon( float((args[1])) , float((args[2])) )
            if( math.pow(E-lastE,2) + math.pow(N-lastN,2) > 0.25  ):
                hdMap.append( (float(args[1]),float(args[2]),float(args[3]),float(args[4])) )
                lastE = E
                lastN = N
        fi.close()
    loadmap()
    print('finished loading map')

    def alpha(ve):
        return 1 * ve

    def searchmap():
        global node
        j = 0
        while True:
            if node['Status'] < 0 or node['Status'] > 2:
                continue
            curDis = 9999
            curPoint = 0
            tarDis = 9999
            tarPoint = 0
            #try:
            easting,northing,zone,zone_letter = UTM.from_latlon(node['Lat'],node['Lon'])
            for i in range(0,len(hdMap)):
                if math.fabs( int(node['Head']  - hdMap[i][2]) ) > 90 :
                    continue
                #get nearest point ---> curPoint
                E,N,Z,Z_l = UTM.from_latlon(hdMap[i][0] ,hdMap[i][1] )
                dis = math.sqrt( math.pow(easting - E,2) + math.pow(northing - N,2)  )
                if dis < curDis:
                    curDis = dis
                    curPoint = i
            #current v
            v = math.sqrt( math.pow( node['V_n'],2 ) + math.pow( node['V_e'],2 )  + math.pow( node['V_earth'],2 ) )
            for i in range(curPoint,len(hdMap)):
                E,N,Z,Z_l= UTM.from_latlon(hdMap[i][0] ,hdMap[i][1] )
                dis = math.fabs( math.sqrt( math.pow(easting - E,2) + \
                      math.pow(northing - N,2)  ) - alpha(v) )
                if dis < tarDis:
                    tarDis = dis
                    tarPoint = i
            dis = curDis
            head = hdMap[tarPoint][2]
            head = head - node['Head']
            if head < -180:
                head = head + 360
            if head > 180:
                head = head - 360
            #hai lun
            if curPoint == 0:
                curPoint = curPoint + 1
            if curPoint == len(hdMap) - 1:
                curPoint = curPoint - 1
            E1,N1,Z1,Z_l1 = \
                             UTM.from_latlon(hdMap[curPoint][0] ,hdMap[curPoint][1] )
            E2,N2,Z2,Z_l2 = \
                             UTM.from_latlon(hdMap[curPoint - 1][0] ,hdMap[curPoint - 1][1] )
            a = math.sqrt( math.pow(easting - E1 ,2)  + math.pow(northing - N1  ,2)  )
            b = math.sqrt( math.pow(easting - E2 ,2)  + math.pow(northing - N2  ,2)  )
            c = math.sqrt( math.pow(E1 - E2 ,2)  + math.pow(N1 - N2  ,2)  )
            p = (a + b + c)/2
            h = math.sqrt(p * (p-a) * (p-b) * (p-c)) * 2 / c
            x1 = (E1 - easting) * math.cos( math.radians(node['Head']) ) - (N1 - northing) * math.sin( math.radians(node['Head']) )
            if x1 < 0:
                dis = dis * -1
                h = h * -1
                pass
            dis = x1
            dhead = 0
            ddhead = 0
            if curPoint + curPoint - tarPoint > 0:
                dhead = hdMap[tarPoint][2]/2 - hdMap[curPoint][2]/2
            if curPoint + curPoint - tarPoint > 0:
                ddhead = hdMap[tarPoint][2]/4 - hdMap[curPoint - 2][2]/2 + hdMap[curPoint - tarPoint + curPoint][2] / 4
            #content = {'Dis':dis,'Head':head,'DHead':dhead,'DDHead':ddhead}
            content = {'Dis':h,'Head':head,'DHead':dhead,'DDHead':ddhead}
            pub.sendPro('Diff',content)
            j = (j + 1) % 9999
            time.sleep(0.05)
            if j%5 ==0:
                print(content)
                print('head = ',node['Head'])
                print('========================================================================================')
            #except Exception:
            #    print("A Error in search map")
    thread.start_new_thread(searchmap, ())

    def draw():
        pygame.init()
        screen = pygame.display.set_mode((1000,600))
        #screen = pygame.display.set_mode((1361,1001))
        pygame.display.set_caption("ququuququququuuq")
        FPS = 50
        fpsClock = pygame.time.Clock()
        BLACK = (0,0,0)
        WHITE = (255,255,255)
        RED = (255,0,0)
        DARKPINK = (255,20,147)
        DARKRED = (138,0,0)
        PURPLE = (160,32,240)
        YELLOW = (255,255,0)
        GREEN = (00,255,0)
        BLUE = (0,0,255)
        LIGHTBLUE = (176,226,255)
        ORANGE4 = (139,69,0)
        screen.fill(BLACK)
        while True:
            screen.fill(BLACK)
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
            mat = []
            centerE,centerN,Z,Z_l = UTM.from_latlon( node['Lat'], node['Lon'] )
            NN = -100 * math.cos( math.radians(node['Head']) )
            EE = 100 * math.sin( math.radians(node['Head']) )
            for content in hdMap:
                E,N,Z,Z_l = UTM.from_latlon( content[0], content[1] )
                #print(E - centerE)
                #mat.append( [int ((E-centerE) * 20) + 300 , int ((N - centerN)* 20)+  300] )
                #print(mat)
                pygame.draw.circle(screen, WHITE, [int ((E-centerE) * 20) + 500 , int (-1 * (N - centerN)* 20)+  300] , 1, 0)
            #pygame.draw.lines(screen, WHITE,False, mat, 1)
            pygame.draw.circle(screen,GREEN,[500,300] , 1 , 0)
            pygame.draw.line(screen, RED, [500, 300], [500 + EE, 300 + NN], 2)
            pygame.display.update()
            fpsClock.tick(FPS)

        pass
    #thread.start_new_thread(draw, ())


    #recieve and search
    ctx = proContext()
    subGPS = ctx.socket(zmq.SUB)
    subGPS.connect('tcp://localhost:8082')
    subGPS.setsockopt(zmq.SUBSCRIBE,'CurGNSS')
    i = 0
    while True:
        node = subGPS.recvPro()
        i = (i+1) % 999
        if i % 20 == 0:
            pass

if __name__ == '__main__':
    main()

