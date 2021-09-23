######### X-Wing flight game client #########


############ CLIENT CONFIGURATION ###########
SERVER_HOSTNAME = "192.168.50.50"
SERVER_PORT = 2021
MUNDO_PORT = 0
TURTLE_SIZE = 20  #tamaño del jugador
WORLD_SIZE = 100  #cuadrado de 100 x 100
#############################################

from socket import *
import threading as th
import logging as log
from pynput import keyboard
import turtle
import xwing,random


angleMap = {'N':90,'E':0,'S':270,'W':180}
quitFlag = False
you = []
friends = {}
def updateScreen(screen,firstMundoCnd):
    firstMundoCnd.wait()
    global you
    global friends
    tartarugas = {}
    tartarugasColor = {}
    oldfriends = {}
    yout = turtle.Turtle(shape="xwing",visible=False)
    yout.color("white")
    yout.resizemode("user")
    yout.turtlesize(2,2,2)
    yout.penup()
    yout.goto((you[0]/(WORLD_SIZE/2))*(screen.window_width()/2-TURTLE_SIZE/2), (you[1]/(WORLD_SIZE/2))*(screen.window_height()/2-TURTLE_SIZE/2))
    yout.tiltangle(angleMap.get(you[2]))
    yout.pendown()
    yout.showturtle()
    turtle.tracer(0,0)
    while True:
        f1=friends.copy()
        s = set(oldfriends) ^ set(f1)
        for x in s:
            if x in f1:
                tartarugas[x]= turtle.Turtle(shape="xwing",visible=False)
                tartarugas[x].resizemode("user")
                tartarugas[x].turtlesize(2,2,2)
                if x in tartarugasColor:
                    tartarugas[x].color('#%02x%02x%02x' % (int(tartarugasColor[x][0][0]*255),int(tartarugasColor[x][0][1]*255),int(tartarugasColor[x][0][2]*255)))
                else:
                    tartarugas[x].color('#%02x%02x%02x' % (random.randrange(40,255,1),random.randrange(40,255,1),random.randrange(40,255,1)))
                tartarugasColor[x] = tartarugas[x].color()
                tartarugas[x].penup()
                tartarugas[x].goto((f1[x][0]/(WORLD_SIZE/2))*(screen.window_width()/2-TURTLE_SIZE/2), (f1[x][1]/(WORLD_SIZE/2))*(screen.window_height()/2-TURTLE_SIZE/2))
                tartarugas[x].tiltangle(angleMap.get(f1[x][2]))
                tartarugas[x].pendown()
                tartarugas[x].showturtle()
            else:
                tartarugas[x].hideturtle()
                del tartarugas[x]
        oldfriends = f1
        for x,t in tartarugas.items():
            t.penup()
            t.goto((oldfriends[x][0]/(WORLD_SIZE/2))*(screen.window_width()/2-TURTLE_SIZE/2), (oldfriends[x][1]/(WORLD_SIZE/2))*(screen.window_height()/2-TURTLE_SIZE/2))
            t.tiltangle(angleMap.get(oldfriends[x][2]))
            t.pendown()
        yout.penup()
        yout.goto((you[0]/(WORLD_SIZE/2))*(screen.window_width()/2-TURTLE_SIZE/2), (you[1]/(WORLD_SIZE/2))*(screen.window_height()/2-TURTLE_SIZE/2))
        yout.tiltangle(angleMap.get(you[2]))
        yout.pendown()
        turtle.update()
        if quitFlag:
            return

def readWorld(clientSkt,firstMundoCnd):
    global you
    global friends
    tic = 0
    while True:
        msg,cli = clientSkt.recvfrom(4048)
        msg = msg.decode().split("\n")
        msg = msg[:-1]
        log.debug("World data received: "+str(msg))
        for x in msg:
            msg0 = x.split(" ")
            if(msg0[0]=="WORLD"):
                if float(float(msg0[1])<float(tic)):
                    log.warning("Received outdated mundo package. Ignoring...")
                    break
                elif float(float(msg0[1])>tic):
                    friends.clear()
                    tic = float(msg0[1])
            elif(msg0[0]=="PLAYER"):
                you = [float(msg0[1]),float(msg0[2]),msg0[3]]
            else:
                friends[msg0[0]] = [float(msg0[1]),float(msg0[2]),msg0[3]]
        firstMundoCnd.set()
        if quitFlag:
            clientSkt.close()
            return




def controlCliente(nombre,retVal: list):
    log.info("Starting control client...")
    try:
        clientSkt = socket(AF_INET,SOCK_STREAM)
    except Exception as e :
        log.fatal("Failed to create socket: socket."+str(e))
        return
    try:
        clientSkt.connect((SERVER_HOSTNAME,SERVER_PORT))
    except Exception as e:
        log.fatal("Failed to connect to control server: "+str(e))

    msg =  "PLAYER " + nombre + "\n"
    msg_bytes = msg.encode()
    msg_size = len(msg_bytes)
    bytesSent = 0
    while(msg_size!=bytesSent):
        try:
            sent = clientSkt.send(msg_bytes[bytesSent:])
        except Exception as e:
            log.fatal("Control connection closed. "+str(e))
            clientSkt.close()
            return
        bytesSent += sent
    object = ""
    while (object.find("\n")==-1):
        try:
            data = clientSkt.recv(4096).decode()
        except Exception as e:
            log.fatal("Control connection closed. "+str(e))
            clientSkt.close()
            return
        object += data
    log.debug("OK RECV: "+object)
    msg0 = object.split("\n")[0]
    msg0 = msg0.split(" ")
    if(msg0[0] != "OK"):
        log.fatal("Server rejected connection: "+msg0[0]+" "+msg0[1])
        clientSkt.close()
        return
    try:
        mundoSkt = socket(AF_INET,SOCK_DGRAM)
        mundoSkt.bind(('',0))
    except Exception as e :
        log.error("Failed to initialize mundo client socket: "+str(e))
    mundoSktPort = mundoSkt.getsockname()
    mundoSktPort = mundoSktPort[1]
    msg =  "LISTEN " + str(mundoSktPort) + "\n"
    msg_bytes = msg.encode()
    msg_size = len(msg_bytes)
    bytesSent = 0
    while(msg_size!=bytesSent):
        try:
            sent = clientSkt.send(msg_bytes[bytesSent:])
        except Exception as e:
            log.fatal("Control connection closed. "+str(e))
            clientSkt.close()
            return
        bytesSent += sent  
    log.debug("MSG SENT: "+msg)
    object = ""
    while (object.find("\n")==-1):
        try:
            data = clientSkt.recv(4096).decode()
        except Exception as e:
            log.warning("Control connection closed. "+str(e))
            clientSkt.close()
            return
        object += data
    if(object!="OK\n"):
        log.warning("Control connection closed. Mundo Listen failure")
        clientSkt.close()
        return
    retVal.append(clientSkt)
    retVal.append(mundoSkt)
    return

def keyCommand(key,clientSkt):
    global quitFlag
    msg = ""
    try:
        if (key.char == "w" or key==keyboard.Key.up):
            msg = "GO N\n" 
        elif (key.char == "a" or key==keyboard.Key.left):
            msg = "GO W\n" 
        elif (key.char == "d" or key==keyboard.Key.right):
            msg = "GO E\n" 
        elif (key.char == "s" or key==keyboard.Key.down):
            msg = "GO S\n"
        elif (key.char == "q" or key==keyboard.Key.esc):
            log.info("Control connection closed by keypress. Shutting down gracefully...")
            quitFlag = True
            clientSkt.close()
            return
    except:
        if (key==keyboard.Key.up):
            msg = "GO N\n" 
        elif (key==keyboard.Key.left):
            msg = "GO W\n" 
        elif (key==keyboard.Key.right):
            msg = "GO E\n" 
        elif (key==keyboard.Key.down):
            msg = "GO S\n"
        elif (key==keyboard.Key.esc):
            log.info("Control connection closed by keypress. Shutting down gracefully...")
            quitFlag = True
            clientSkt.close()
            return
    msg_bytes = msg.encode()
    msg_size = len(msg_bytes)
    bytesSent = 0
    while(msg_size!=bytesSent):
        try:
            sent = clientSkt.send(msg_bytes[bytesSent:])
        except Exception as e:
            log.fatal("Control connection closed. "+str(e))
            clientSkt.close()
            return
        bytesSent += sent  
    if(msg_size>0):
        log.info("New command: "+msg)

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
                                [`-.|__________ll_|      X-Wing Flight Client
                              ,'    ,' `.        `.      By Grupo06
                            ,'    ,'     `.    ____`.    Curso Redes de computadoras FING-UDELAR
                -)---------========        `.  `.____`.
                                             `.        `.
    By Grupo06                                 `.________`.
                              --)-------------|___________|
    """)
    username = input("Ingrese su username: ")
    log.basicConfig(format='%(levelname)s- %(message)s')
    log.root.setLevel(log.INFO)
    retVal = []
    ctrlCliente = th.Thread(target=controlCliente,args=(username,retVal))
    ctrlCliente.start()
    ctrlCliente.join()
    if(len(retVal)!=2):
        log.fatal("Control connection failed. Quitting...")
        return -1
    log.info("Control connection successful. Listening keyboard")
    listener = keyboard.Listener(on_press=lambda event: keyCommand(event,retVal[0]))
    listener.start()
    firstMundoCnd = th.Event()
    readWorldth = th.Thread(target=readWorld,args=(retVal[1],firstMundoCnd))
    readWorldth.start()

    screen = turtle.Screen()
    screen.setup(1000,1000)
    screen.addshape("xwing",xwing.Xwing)
    screen.bgpic("bg.gif")
    updateScreen(screen,firstMundoCnd)
    listener.stop()
    readWorldth.join()
    screen.bye()
    return 0

if __name__ == "__main__":
    main()
