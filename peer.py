import sys
import socket
import threading
import queue
import time
import os

my_uuid= os.popen("wmic diskdrive get serialnumber").read().split()[-1]               #peer'ın uuid'si tutuluyor.(harddisk'e göre)

class loggerThread(threading.Thread):                                                 #Peer'ın log dosyasını tutmak için oluşturulmuş
    def __init__(self, name, logQueue, logName):                                      # Thread'dir. log_client.txt dosyasının içine yazar.
        threading.Thread.__init__(self)
        self.name = name
        self.lQueue = logQueue
        self.fid = open(logName, "a+")

    def log(self, message):
        t = time.ctime()
        print( t + ":" + message )
        self.fid.write( t + ":" + message + "\n")
        self.fid.flush()

    def run(self):
        self.log("Starting " + self.name)
        while True:
            if not self.lQueue.empty():
                to_be_logged = self.lQueue.get()
                self.log(to_be_logged)
        self.log("Exiting" + self.name)
        self.fid.close()

class readerThread (threading.Thread):

    def __init__(self, name, csoc, senderQueue):
        threading.Thread.__init__(self)
        self.name = name
        self.csoc = csoc
        self.senderQueue = senderQueue

    def incoming_parser(self, data):
        rest=data[4:]
        print(data)

        if data[0:3] == "ERL":
            msg = "Öncelikle giriş yapmalısınız"
            print(msg)
            self.senderQueue.put(msg)

        if data[0:3] == "ERR":
            msg = "Hatalı komut"
            print(msg)
            self.senderQueue.put(msg)

        if data[0:3] == "HEL":
            msg = "Yeni kullanıcı kabul edildi"
            print(msg)
            self.senderQueue.put(rest + " kullanıcısı kabul edildi")

        if data[0:3] == "TOC":
            msg = "Bağlantı testi yapıldı, konuştuğum kişinin uuid'si:" + rest
            print(msg)
            self.senderQueue.put(msg)


        if data[0:3] == "LSA":
            msg = "Kullanıcı listesi isteme"
            print(msg)
            self.senderQueue.put(msg+ "---"+rest)


        if data[0:3] == "BYE":
            msg ="Çıkış yapılıyor"
            print(msg)
            self.senderQueue.put(msg)
            time.sleep(0.3)
            exit()

    def run(self):
        while True:
            data = self.csoc.recv(1024)
            self.message = self.incoming_parser(data.decode())
            if self.message==-1:
                break
        s.close()

class senderThread (threading.Thread):

    def __init__(self, name, csoc, threadQueue):
        threading.Thread.__init__(self)
        self.name = name
        self.csoc = csoc
        self.senderQueue=threadQueue

    def run(self):
        while True:
            time.sleep(0.5)
            queue_message = input("Girdi\n")
            self.out_going(queue_message)

    def out_going(self,data):
        komut = data[0:3]

        if komut == "USR":
            uuid, type = data[3:].split(",")
            msg = "USR " + uuid + "," + type
            print(msg)
            self.csoc.send(msg.encode())
            lQueue.put("***RECV: " + msg)

        if komut == "TIC":
            msg = "TIC " + my_uuid
            self.csoc.send(msg.encode())
            lQueue.put("***RECV: " + msg)

        if komut == "LSQ":
            msg = "LSQ"
            self.csoc.send(msg.encode())
            lQueue.put("***RECV: " + msg)

        if komut == "QUI":
            msg = "QUI"
            self.csoc.send(msg.encode())
            lQueue.put("***RECV: " + msg)



lQueue = queue.Queue()
lThread = loggerThread("Logger", lQueue, "log_client.txt")
lThread.start()

senderQueue = queue.Queue(20)

s = socket.socket()
host = "127.0.0.1"
port = 12345
s.connect((host,port))
st = senderThread("senderThread", s, senderQueue)
st.start()
rt = readerThread("ReaderThread", s, senderQueue)
rt.start()
st.join()
rt.join()
s.close()






