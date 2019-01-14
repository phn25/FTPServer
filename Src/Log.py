# Phuong Nguyen
# CS472 - HW3
# Program: Log.py
# 11/12/2018

import socket
import datetime
import time

class Log:
    def __init__(self):
        self.fileName = ''
        self.logFile = None

    def setAndOpenFile(self, fileName):
        self.fileName = fileName
        self.logFile = open(fileName, "w")

    def logConnectionInfo(self, connInfo, port):
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        self.logFile.writelines(st + " Got connection from " + connInfo + " on port " + str(port) + "\n")
    
    def log(self, method, message):
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        self.logFile.writelines(st + " " + method + ": " + message + "\n")

    def log_(self, message):
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        self.logFile.writelines(st + " " + message + "\n")

    def append(self, message):
        self.logFile.writelines(message + "\n")

    def close(self):
        self.logFile.close()
