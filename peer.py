import socket
import threading
import queue
import time
import os
import hashlib
from difflib import SequenceMatcher
import datetime

my_uuid = os.popen("wmic diskdrive get serialnumber").read().split()[-1]  # peer'ın uuid'si tutuluyor.(harddisk'e göre)


class loggerThread(threading.Thread):                                   # Peer'ın log dosyasını tutmak için oluşturulmuş

    def __init__(self, name, logQueue, logName):  # Thread'dir. log_client.txt dosyasının içine yazar.
        threading.Thread.__init__(self)
        self.name = name
        self.lQueue = logQueue
        self.fid = open(logName, "a+")

    def log(self, message):
        t = time.ctime()
        print(t + ":" + message)
        self.fid.write(t + ":" + message + "\n")
        self.fid.flush()

    def run(self):
        self.log("Starting " + self.name)
        while True:
            if not self.lQueue.empty():
                to_be_logged = self.lQueue.get()
                self.log(to_be_logged)
        self.log("Exiting" + self.name)
        self.fid.close()

class server_thread(threading.Thread):

    def __init__(self, name, csoc, fihrist, sendQueue, logQueue):
        threading.Thread.__init__(self)
        self.name = name
        self.csoc = csoc
        self.fihrist = fihrist
        self.sendQueue = sendQueue
        self.logQueue = logQueue
        self.uuid = ""
        self.ip = ""
        self.port = ""
        self.type = ""
        self.ip_buffer = ""
        self.port_buffer = ""

    def parser(self, data):
        if len(data) != 0:
            if len(data) < 3:
                msg = "ERR"
                return msg

            if data[0:3] == "USR":
                self.type, self.uuid = data[4:].split(",")
                self.ip_buffer, self.port_buffer = str(addr[0:]).split(",")
                self.ip = self.ip_buffer[2:-1]
                self.port = self.port_buffer[1:-1]
                self.timestamp = time.ctime()


                if len(data) < 4:                                                       #ip,port ve type bilgilerini kesin verdi mi kontrolü yapılmalı.
                    self.logQueue.put("Error because of lenght")
                    msg = "ERR"
                    return msg


                elif len(self.ip) < 7:                                                    # 0.0.0.0 minimum 7 karakterden oluşur gibi basit bir şey düşündüm,
                    self.logQueue.put("IP bilgisi yanlış")                              # geliştirilmeye açık..
                    msg = "ERR"
                    return msg

                elif self.type != "peer":
                    self.logQueue.put("Tanımlı olmayan bir type ile kayıt olmaya çalışıyorsunuz")
                    msg = "ERR"
                    return msg

                elif self.uuid in self.fihrist.keys():
                    self.logQueue.put("Listemde zaten bulunmaktasın ama yine de hoşgeldin : " + self.uuid)
                    msg = "HEL " + self.uuid
                    return msg

                else:
                    self.logQueue.put(self.uuid + " joined system as a " + self.type)
                    fihrist[self.uuid] = self.ip +" " + self.port + " " + self.type + " " + self.timestamp
                    # print(fihrist)        #giriş yapanları yazıyorum.

                    msg = "HEL " + self.uuid +" " + self.type +" " + self.timestamp
                    return msg

            if data[0:3] == "TIC":                                                    #kendi uuidsini eklesin
                self.timestamp = time.ctime()                                         # zaman güncellenir.
                self.logQueue.put(self.uuid + " said TIC")
                msg = "TOC " + str(my_uuid)
                return msg

            if data[0:3] == "LSQ":
                response = ""
                for i in self.fihrist.keys():
                    response += "\n" + i + " " + self.fihrist[i]
                response_list = str(response)
                self.logQueue.put(self.uuid+ " wants to know online user"+ response_list[1:])
                msg = "LSA " + response_list[1:]
                return msg


            if data[0:3] == "SRC":

                files = os.listdir('C:\\Users\\kerem\\PycharmProjects\\Dagıtık_Proje\\shared')
                print(files)
                filename = data[4:]

                def benzerlik(first_file, second_file):

                    first_file = first_file.lower()
                    second_file = second_file.lower()
                    benzer = SequenceMatcher(None, first_file, second_file).ratio()
                    return (1 - benzer)

                file_info = []
                file_indices = []
                md5_info = []
                properties = []
                boyut = []
                tarih = []
                sorted_array = []
                sozluk = dict()
                md5_all = []

                def search_files(filename):

                    for file in files:
                        benzerlik_orani = benzerlik(filename, file)
                        file_md5_all = get_md5(file)
                        md5_all.append(file_md5_all)
                        if benzerlik_orani <= 0.7:
                            file_indices.append(benzerlik_orani)
                            file_info.append(file)
                            file_md5 = get_md5(file)
                            sozluk[file_md5] = file
                            md5_info.append(file_md5)
                            properties = os.stat('C:\\Users\\kerem\\PycharmProjects\\Dagıtık_Proje\\shared\\' + file)
                            boyut.append(properties.st_size)
                            tarih.append(datetime.datetime.fromtimestamp(properties.st_ctime))
                        else:
                            pass

                    if not file_info:
                        msg= "YOK"
                        self.csoc.send(msg.encode())

                    for i in range(len(file_indices)):
                        minimum = i
                        for j in range(i + 1, len(file_indices)):
                            if file_indices[minimum] > file_indices[j]:
                                minimum = j
                        file_indices[i], file_indices[minimum] = file_indices[minimum], file_indices[i]

                    print("Sorted array")
                    for i in range(len(file_indices)):
                        sorted_array.append(file_info[i] + "  " + md5_info[i] + "  " + str(tarih[i]) + "  " + str(boyut[i]) + " KB")
                        print(sorted_array)



                def get_md5(filename):
                    md5_chechsum = hashlib.md5(open("C:\\Users\\kerem\\PycharmProjects\\Dagıtık_Proje\\shared\\" +
                                                    filename, 'rb').read()).hexdigest()
                    return md5_chechsum

                def search_md5(choosen_md5):

                    for buffer_md5 in md5_all:
                        if choosen_md5 in buffer_md5:
                            print("var ahanda bu:  " + sozluk[choosen_md5])
                            break
                        else:
                            print("yok")

                search_files(filename)
                msg = "VAR " + str(sorted_array)
                self.csoc.send(msg.encode())
                choosen_md5="29629bbdff61a8fde6eb0a0c4260f1b9"
                search_md5(choosen_md5)



            if data[0:3] == "QUI":                                             #çıkış kısmını kontrol et.
                message = self.uuid + " left."
                self.logQueue.put(message)
                msg = "BYE " + self.uuid
                self.csoc.send(msg.encode())
                del self.fihrist[self.uuid]
                send_message = ("SYS", self.uuid, message)
                for q in self.fihrist.values():
                    q.put(send_message)
                msg = "QUI"
                return msg

            else:
                return "ERR"
        else:
            return "ERL"

    def run(self):
        self.logQueue.put(self.name + ": starting.")
        while True:
            data = self.csoc.recv(1024)
            msg = self.parser(data.decode()) + "\n"
            if msg == "QUI":  # Çıkış işlemi geldiyse soketi de kapatıp çıkar.
                self.sendQueue.put("QUI")
                self.csoc.close()
                break
            self.csoc.send(msg.encode())
        self.logQueue.put(self.name + ": exiting.")

class readerThread (threading.Thread):

    def __init__(self, name, csoc, host, port, senderQueue):
        threading.Thread.__init__(self)
        self.name = name
        self.csoc = csoc
        self.senderQueue = senderQueue
        self.host = host
        self.port = port

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

        if data[0:3] =="VAR":
            dosya_adi =data[6:-2]
            msg = "Dosya sorgulama isteği"
            print("Bulunan dosyalar: \n" + dosya_adi)
            self.senderQueue.put(msg)


        if data[0:3] == "BYE":
            msg ="Çıkış yapılıyor"
            print(msg)
            self.senderQueue.put(msg)
            time.sleep(0.3)
            exit()

    def run(self):
        # self.csoc = socket.socket()
        self.csoc.connect((self.host, int(self.port)))

        while True:
            data = self.csoc.recv(1024)
            self.message = self.incoming_parser(data.decode())
            if self.message==-1:
                break
        s.close()

class senderThread (threading.Thread):

    def __init__(self, name, csoc, host, port, threadQueue,data):
        threading.Thread.__init__(self)
        self.name = name
        self.csoc = csoc
        self.senderQueue = threadQueue
        self.host = host
        self.port = port
        self.data = data

    def run(self):
        while True:

            if not self.senderQueue.empty():
                self.queue_message = self.senderQueue.get()
                self.out_going(self.queue_message)

    def out_going(self, data):
        komut = data[0:3]


        if komut == "USR":
            msg = data
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

        if komut == "SRC":
            dosya_adi = data[6:-2]
            msg = "SRC " + dosya_adi
            self.csoc.send(msg.encode())
            lQueue.put("***RECV: " + msg)

class clienthandlerThread(threading.Thread):

    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):

        while True:
            choice = input("hangi seneryo: ")
            self.chooser(choice)
            time.sleep(1)

    def chooser(self, data):

        if data[0:3] == "TIC":
            self.host,self.port = data [4:].split(",")
            self.gonderilecek = data[0:3] + my_uuid
            self.senderQueue = queue.Queue(20)
            self.handlerSocket = socket.socket()
            self.rthread = readerThread("ReaderThread", self.handlerSocket, self.host, self.port, self.senderQueue)
            self.rthread.start()
            self.senderQueue.put(self.gonderilecek)
            self.sthread = senderThread("SenderThread", self.handlerSocket, self.host, self.port, self.senderQueue, self.gonderilecek)
            self.sthread.start()

        if data[0:3] =="USR":
            self.host, self.port, self.type = data[4:].split(",")
            self.gonderilecek = data[0:3] +" " + self.type +","+ my_uuid
            self.senderQueue = queue.Queue(20)
            self.handlerSocket = socket.socket()
            self.rthread = readerThread("ReaderThread", self.handlerSocket, self.host, self.port, self.senderQueue)
            self.rthread.start()
            self.senderQueue.put(self.gonderilecek)
            self.sthread = senderThread("SenderThread", self.handlerSocket, self.host, self.port, self.senderQueue,
                                        self.gonderilecek)
            self.sthread.start()

        if data[0:3] == "SRC":
            self.filename = data[4:].split(",")
            print(self.host)
            print(self.port)
            print(self.filename)
            self.gonderilecek = data[0:3] + " " + str(self.filename)
            self.senderQueue = queue.Queue(20)
            self.handlerSocket = socket.socket()
            self.rthread = readerThread("ReaderThread", self.handlerSocket, self.host, self.port, self.senderQueue)
            self.rthread.start()
            self.senderQueue.put(self.gonderilecek)
            self.sthread = senderThread("SenderThread", self.handlerSocket, self.host, self.port, self.senderQueue,
                                        self.gonderilecek)
            self.sthread.start()

        if data[0:3] == "LSQ":
            self.gonderilecek = data[0:3]
            self.senderQueue = queue.Queue(20)
            self.handlerSocket = socket.socket()
            self.rthread = readerThread("ReaderThread", self.handlerSocket, self.host, self.port, self.senderQueue)
            self.rthread.start()
            self.senderQueue.put(self.gonderilecek)
            self.sthread = senderThread("SenderThread", self.handlerSocket, self.host, self.port, self.senderQueue,
                                        self.gonderilecek)
            self.sthread.start()

        if data[0:3] == "QUI":
            self.gonderilecek = data[0:3]
            self.senderQueue = queue.Queue(20)
            self.handlerSocket = socket.socket()
            self.rthread = readerThread("ReaderThread", self.handlerSocket, self.host, self.port, self.senderQueue)
            self.rthread.start()
            self.senderQueue.put(self.gonderilecek)
            self.sthread = senderThread("SenderThread", self.handlerSocket, self.host, self.port, self.senderQueue,
                                        self.gonderilecek)
            self.sthread.start()


fihrist = dict()
lQueue = queue.Queue()
lThread = loggerThread("Logger", lQueue, "log_client.txt")
lThread.start()

server_queue = queue.Queue(20)

s = socket.socket()
host_serv = "0.0.0.0"
port_serv = 12350
s.bind((host_serv, port_serv))
s.listen(5)

cht = clienthandlerThread("ClienthandlerThread")
cht.start()

serverCounter = 1
while True:
    c, addr = s.accept()
    print("Got connection from " +str(addr))
    serv_thr = server_thread("Server Thread" + str(serverCounter), c, fihrist, server_queue, lQueue)
    serv_thr.start()
    serverCounter += 1

rt.join()
st.join()
s.close()




