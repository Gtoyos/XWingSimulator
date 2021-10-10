######### X-Wing flight game server #########

############ SERVER CONFIGURATION ###########
CONTROL_PORT = 2021
SPEED_CONTROL = 1
DELTATIME_CONTROL = 0.01
VISUAL_RANGE = 15
MAX_CONNECTIONS_PER_HOST = 2000
DESIREDMAX_UDP_MSGSIZE = 32768
MAX_USERNAME_LEN = 300
ENABLE_BOTCHK = False
#############################################


import _thread as thread
import queue
import random,time,re,numpy
from socket import *
import logging as log
import threading as th
import math

### Mundo = {username: [hostname,port,x,y,direction]}
Mundo = {}
Broadcasters = {}
MundoLock = thread.allocate_lock()

def botChk(clientHost,clientPort):
    if(not ENABLE_BOTCHK):
        return True
    i=0
    for x,y in Mundo.items():
        if y[0]==clientHost and y[1]==clientPort:
            i+=1
            if i>MAX_CONNECTIONS_PER_HOST:
                return False
    return True
def usernameChk(username):
    return not (username in Mundo)
def mundoPortChk(clientHost,clientPort):
    if(not ENABLE_BOTCHK):
        return True
    for x,y in Mundo.items():
        if y[0]==clientHost and y[1]==clientPort:
            return False
    return True

def mundoBroadcaster(username,clientHost,clientPort):
    global Broadcasters
    try:
        serverSkt = socket(AF_INET,SOCK_DGRAM)
    except Exception as e :
        log.error("Failed to initialize mundoBroadcast socket: "+str(e))
    while True:
        M = Mundo #Solo lectura
        you = M[username]
        friends = []
        for key,value in M.items():
            if key!=username and math.sqrt((you[2]-value[2])**2 + (you[3]-value[3])**2)<=VISUAL_RANGE:
                friends.append([key,value])
        msgHead = "WORLD "+str(time.time())+"\nPLAYER "+str(you[2])+" "+str(you[3])+" "+str(you[4])+"\n"
        msgHead = msgHead.encode()
        msg=""
        i=0
        for f in friends:
            msg += str(f[0])+" "+str(f[1][2])+" "+str(f[1][3])+" "+str(f[1][4])+"\n"
            msgb = msg.encode()
            msgbl = len(msgHead)+len(msgb)
            i+=1
            if(msgbl>=DESIREDMAX_UDP_MSGSIZE or i==len(friends)):
                bsent=0
                msgb=msgHead+msgb
                while(msgbl!=bsent):
                    try:
                        b=serverSkt.sendto(msgb[bsent:],(clientHost,clientPort))
                    except Exception as e:
                        log.error("Brodcaster for "+username+" has failed: "+str(e))
                        serverSkt.close()
                        Broadcasters[username]=-1
                        return
                    bsent += b
                msg=""
        if len(friends)==0:
            msgb = msgHead
            msgbl = len(msgb)
            bsent=0
            while(msgbl!=bsent):
                try:
                    b=serverSkt.sendto(msgb[bsent:],(clientHost,clientPort))
                except Exception as e:
                    log.error("Brodcaster for "+username+" has failed: "+str(e))
                    serverSkt.close()
                    Broadcasters[username]=-1
                    return
                bsent += b
        if Broadcasters[username]==0:
            log.info("Stopped broadcaster for "+username+".")
            serverSkt.close()
            return
        time.sleep(DELTATIME_CONTROL)

def procesarComandos(commandBuffer: queue.Queue,username,clientHost,clientPort):
    MundoLock.acquire()
    while(not commandBuffer.empty()):
        c = commandBuffer.get()
        new_direction = c.split(" ")[1]
        Mundo[username][4]=new_direction
    MundoLock.release()

def crearUsuario(username,hostname,port):
    MundoLock.acquire()
    Mundo[username] = [hostname,port,random.randrange(-40,40,1),random.randrange(-40,40,1),random.choice(["N","S","E","W"])]
    MundoLock.release()

def atenderCliente(clientSkt: socket):
    global Broadcasters
    log.info("New control connection on: "+str(clientSkt.getpeername()))
    object = ""
    while (object.find("\n")==-1):
        try:
            data = clientSkt.recv(4096).decode()
        except Exception as e:
            log.warning("Control connection closed. "+str(e))
            clientSkt.close()
            return
        object += data
    msg0 = object.split("\n")[0] #no debería ser necesario
    msg0 = msg0.split(" ")
    clientHost,clientPort = clientSkt.getpeername()
    msg = ""
    if(msg0[0]!="PLAYER"):
        msg = "FAIL BAD_FORMAT\n"
    elif(not botChk(clientHost,clientPort)):
        msg = "FAIL BOT_BLOCKED\n"
    elif(not usernameChk(msg0[1])):
        msg = "FAIL USERNAME_IN_USE\n"
    elif(len(msg0[1].encode())>MAX_USERNAME_LEN):
        msg = "FAIL USERNAME_TOOLARGE\n"
    else:
        msg = "OK\n"
    msg_bytes = msg.encode()
    msg_size = len(msg_bytes)
    bytesSent = 0
    while(msg_size!=bytesSent):
        try:
            sent = clientSkt.send(msg_bytes[bytesSent:])
        except Exception as e:
            log.warning("Control connection closed. "+str(e))
            clientSkt.close()
            return
        bytesSent += sent
    if(msg.split(" ")[0]=="FAIL"):
        log.info("Connection rejected: "+msg)
        clientSkt.close()
        return
    log.info("Control answer for @"+msg0[1]+": "+msg[:-1])
    objectPort = ""
    while (objectPort.find("\n")==-1):
        try:
            data = clientSkt.recv(4096).decode()
        except Exception as e:
            log.warning("Control connection closed. "+str(e))
            clientSkt.close()
            return
        objectPort += data
    clientPort = objectPort.split("\n")[0].split(" ")[1]
    clientPort = int(clientPort)
    log.info("@"+msg0[1]+" requested broadcast at port "+str(clientPort))
    if(not mundoPortChk(clientHost,clientPort)):
        msg="FAIL MUNDO_PORT_IN_USE\n"
    else:
        msg = "OK\n"
    log.info("Control listen answer: "+msg[:-1])
    msg_bytes = msg.encode()
    msg_size = len(msg_bytes)
    bytesSent = 0
    while(msg_size!=bytesSent):
        try:
            sent = clientSkt.send(msg_bytes[bytesSent:])
        except Exception as e:
            log.warning("Control connection closed. "+str(e))
            clientSkt.close()
            return
        bytesSent += sent
    if(msg == "FAIL MUNDO_PORT_IN_USE\n"):
        log.warning("Control connection closed. ")
        clientSkt.close()
        return
    crearUsuario(msg0[1],clientHost,clientPort)
    log.info("A new player has joined: "+msg0[1]+" on "+clientHost+":"+str(clientPort))
    commandBuffer = queue.Queue()
    Broadcasters[msg0[1]] = 1
    mundoBroadcast = th.Thread(target=mundoBroadcaster,args=(msg0[1],clientHost,clientPort))
    mundoBroadcast.start()
    while True:
        while (object.find("\n")==-1):
            try:
                data = clientSkt.recv(4096).decode() #ERROR?
            except Exception as e:
                log.info("Control connection closed. "+str(e))
                clientSkt.close()
                Broadcasters[msg0[1]] = 0
                mundoBroadcast.join()
                log.info("Control connection for "+msg0[1]+" ended gracefully.")
                MundoLock.acquire()
                Mundo.pop(msg0[1])
                MundoLock.release()
                return
            if data == "":
                log.info("Control connection closed. EOF received")
                clientSkt.close()
                Broadcasters[msg0[1]] = 0
                mundoBroadcast.join()
                log.info("Control connection for "+msg0[1]+" ended gracefully.")
                MundoLock.acquire()
                Mundo.pop(msg0[1])
                MundoLock.release()
                return                
            object += data
        comandos = object.split("\n")
        for x in comandos[:-1]:
            if re.match(r"^GO\s[NSEW]$", x):
                commandBuffer.put(x)
        if comandos[-1] != "":
            object = comandos[-1]
        else:
            object = ""
        procesarComandos(commandBuffer,msg0[1],clientHost,clientPort)
        if Broadcasters[msg0[1]] == -1:
            clientSkt.close()
            log.info("Control connection for "+msg0[1]+" ended gracefully.")
            MundoLock.acquire()
            Mundo.pop(msg0[1])
            MundoLock.release()
            return

def controlListener():
    log.info("Starting control server...")
    try:
        serverSkt = socket(AF_INET,SOCK_STREAM)
        serverSkt.bind(('',CONTROL_PORT))
    except Exception as e :
            log.root.fatal("Failed to create socket: socket."+str(e))
            return
    serverSkt.listen(5)
    log.info("Control server initialized.")
    while(True):
            clientSkt, addr = serverSkt.accept()
            th.Thread(target=atenderCliente,args=(clientSkt,)).start()
    serverSkt.close()
    return

#SIMULADOR DEL MUNDO
def mundoSimulator():
    while True:
        MundoLock.acquire()
        for user,v in Mundo.items():
            if v[4]=="N":
                v[3] += SPEED_CONTROL*DELTATIME_CONTROL
            elif v[4]=="S":
                v[3] -= SPEED_CONTROL*DELTATIME_CONTROL
            elif v[4]=="E":
                v[2] += SPEED_CONTROL*DELTATIME_CONTROL
            elif v[4]=="W":
                v[2] -= SPEED_CONTROL*DELTATIME_CONTROL
            if(v[3])>50:
                v[3]=-50
            if(v[3])<-50:
                v[3]=50
            if(v[2])>50:
                v[2]=-50
            if(v[2])<-50:
                v[2]=50
            #v[3]=numpy.clip(v[3],-50,50)
            #v[2]=numpy.clip(v[2],-50,50)
        MundoLock.release()
        time.sleep(DELTATIME_CONTROL)
        log.debug("Mundo="+str(Mundo))


def main():
    print("""
                                --)-----------|____________|
                                              ,'       ,'
                -)------========            ,'  ____ ,'
                         `.    `.         ,'  ,'__ ,'
                           `.    `.     ,'       ,'
                             `.    `._,'_______,'__
                               [._ _| ^--      || |
                       ____,...-----|__________ll_|\\
      ,.,..-------\"\"\"\"\"     \"----'                 ||
  .-""  |=========================== ______________ |
   "-...l_______________________    |  |'      || |_]
                                [`-.|__________ll_|      X-Wing Flight Server
                              ,'    ,' `.        `.      By Grupo06
                            ,'    ,'     `.    ____`.    Curso Redes de computadoras FING-UDELAR
                -)---------========        `.  `.____`.
                                             `.        `.
    By Grupo06                                 `.________`.
                              --)-------------|___________|
    """)
    log.basicConfig(format='%(levelname)s- %(message)s')
    log.root.setLevel(log.INFO)
    th.Thread(target=controlListener).start()
    th.Thread(target=mundoSimulator).start()

if __name__ == "__main__":
    main()

