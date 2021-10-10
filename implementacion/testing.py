# PERFORMANCE TEST FOR X-WING CLIENTE/SERVER

import cliente
import random,time
from pynput import keyboard

def main():
    print("-XWING Benchmark test-")
    x=input("X-wings to generate: ")
    x=int(x)
    ctrl_sockets=[]
    for i in range(0,x):
        us = "player_"+str(i)
        retVal = []
        cliente.controlCliente(us,retVal)
        if(len(retVal)>0):
            ctrl_sockets.append(retVal[0])
        retVal.clear()
    print("Finished to generate "+str(x)+" X-Wings. Starting random flight...")
    while True:
        for x in ctrl_sockets:
            cliente.keyCommand(random.choice([keyboard.Key.up,keyboard.Key.down,keyboard.Key.left,keyboard.Key.right]),x)
        time.sleep(1)
if __name__ == "__main__":
    main()
