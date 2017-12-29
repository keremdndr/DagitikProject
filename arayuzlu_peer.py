import socket
import threading
import queue
import time
import uuid
import json
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
import os
from difflib import SequenceMatcher
import datetime
import hashlib

fihrist = dict()
my_uuid = uuid.uuid4()
PORT =12350
lQueue=queue.Queue()
file_dict = dict()

class loggerThread(threading.Thread):

    def __init__(self, name, logQueue, logName):
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

    def run(self):
        self.logQueue.put(self.name + ": starting.")
        while True:
            data = self.csoc.recv(1024)
            msg = self.parser(data.decode()) + "\n"
            if msg == "QUI":
                self.sendQueue.put("QUI")
                self.csoc.close()
                break
            self.csoc.send(msg.encode())
        self.logQueue.put(self.name + ": exiting.")

    def parser(self, data):
        if len(data) != 0:
            if len(data) < 3:
                msg = "ERR"
                return msg

            if data[0:3] == "USR":
                dat = data[4:].split(",")
                self.uuid = dat[0]
                print(self.uuid)
                dat.pop(0)
                self.port = dat[0]
                print(self.port)
                dat.pop(0)
                self.ip = dat[0]
                print(self.ip)
                dat.pop(0)
                self.type = dat[0]
                print(self.type)
                self.timestamp = time.ctime()

                if self.type != "peer":
                    self.logQueue.put("Tanımlı olmayan bir type ile kayıt olmaya çalışıyorsunuz")
                    msg = "ERR"
                    return msg

                if self.uuid in self.fihrist.keys():
                    self.logQueue.put("Listemde zaten bulunmaktasın ama yine de hoşgeldin : " + self.uuid)
                    msg = "HEL " + self.uuid
                    return msg

                else:
                    self.logQueue.put(self.uuid + " joined system as a " + self.type)
                    fihrist[self.uuid] = str(self.ip) + " " + str(self.port) + " " + str(
                        self.type) + " " + self.timestamp
                    msg = "HEL " + self.uuid + " " + self.ip + " " + self.port + " " + self.type + " " + self.timestamp
                    return msg

            if data[0:3] == "TIC":
                self.timestamp = time.ctime()
                self.logQueue.put(self.uuid + " said TIC")
                msg = "TOC " + str(my_uuid)
                return msg

            if data[0:3] == "LSQ":
                response = ""
                for i in self.fihrist.keys():
                    response += "\n" + i + " " + self.fihrist[i]
                print(fihrist)
                response_list = str(response)
                self.logQueue.put(self.uuid + " wants to know online user" + response_list[1:])
                data_string = json.dumps(fihrist)
                msg = "LSA " + data_string
                return msg

            if data[0:3] == "SRC":
                files = os.listdir('C:\\Users\\asus\\PycharmProjects\\untitled\\shared\\')
                print(files)
                filename = data[4:]
                file_info = []
                file_indices = []
                md5_info = []
                properties = []
                boyut = []
                tarih = []
                sorted_array = []
                sozluk = dict()
                md5_all = []

                def benzerlik(first_file, second_file):

                    first_file = first_file.lower()
                    second_file = second_file.lower()
                    benzer = SequenceMatcher(None, first_file, second_file).ratio()
                    return (1 - benzer)

                def search_files(filename):

                    for file in files:
                        benzerlik_orani = benzerlik(filename, file)
                        if benzerlik_orani <= 0.7:
                            file_indices.append(benzerlik_orani)
                            file_info.append(file)
                            file_md5 = get_md5(file)
                            sozluk[file_md5] = file
                            md5_info.append(file_md5)
                            properties = os.stat("C:\\Users\\asus\\PycharmProjects\\untitled\\shared\\" + file)
                            boyut.append(properties.st_size)
                            tarih.append(datetime.datetime.fromtimestamp(properties.st_ctime))
                        else:
                            pass

                    if not file_info:
                        msg = "YOK"
                        self.csoc.send(msg.encode())

                    for i in range(len(file_indices)):
                        minimum = i
                        for j in range(i + 1, len(file_indices)):
                            if file_indices[minimum] > file_indices[j]:
                                minimum = j
                        file_indices[i], file_indices[minimum] = file_indices[minimum], file_indices[i]

                    print("Sorted array")
                    for i in range(len(file_indices)):
                        sorted_array.append(
                            file_info[i] + "  " + md5_info[i] + "  " + str(tarih[i]) + "  " + str(boyut[i]) + " KB")
                        print(sorted_array)

                def get_md5(filename):
                    md5_chechsum = hashlib.md5(open('C:\\Users\\asus\\PycharmProjects\\untitled\\shared\\' +
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
                dosya_dic = json.dumps(sozluk)
                msg = dosya_dic
                print("VAAAARR")
                return "VAR " + msg

            if data[0:3] == "QUI":                                                  #çıkış kısmını kontrol et.
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
            if msg == "QUI":
                self.sendQueue.put("QUI")
                self.csoc.close()
                break
            self.csoc.send(msg.encode())
        self.logQueue.put(self.name + ": exiting.")

class server_starter(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        fihrist = dict()
        lQueue = queue.Queue()
        lThread = loggerThread("Logger", lQueue, "log_client.txt")
        lThread.start()
        server_queue = queue.Queue(20)
        s = socket.socket()
        host_serv = "0.0.0.0"
        port_serv = PORT
        s.bind((host_serv, port_serv))
        s.listen(5)
        serverCounter = 1
        while True:
            c, addr = s.accept()
            print("Got connection from " + str(addr))
            serv_thr = server_thread("Server Thread" + str(serverCounter), c, fihrist, server_queue, lQueue)
            serv_thr.start()
            serverCounter += 1

class readerThread (threading.Thread):

    def __init__(self, name, csoc, host, senderQueue):
        threading.Thread.__init__(self)
        self.name = name
        self.csoc = csoc
        self.senderQueue = senderQueue
        self.host = host
        self.port = str(PORT)

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
            msg = json.loads(rest)

            self.senderQueue.put(msg)

        if data[0:3] =="VAR":
            msg = json.loads(rest)
            file_dict = msg
            time.sleep(5)
            self.senderQueue.put(msg)

        if data[0:3] == "BYE":
            msg ="Çıkış yapılıyor"
            print(msg)
            self.senderQueue.put(msg)
            time.sleep(0.3)
            exit()

    def run(self):
        global file_dict
        while True:
            data = self.csoc.recv(1024)
            self.message = self.incoming_parser(data.decode())
            if self.message==-1:
                break
        self.csoc.close()

class senderThread (threading.Thread):

    def __init__(self, name, csoc, host, threadQueue):
        threading.Thread.__init__(self)
        self.name = name
        self.csoc = csoc
        self.senderQueue = threadQueue
        self.host = host
        self.port = str(PORT)

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
            msg = "TIC " + str(my_uuid)
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

    def __init__(self, name, host, port, queue, fileName):
        threading.Thread.__init__(self)
        self.name = name
        self.host = host
        self.port = port
        self.client_queue = queue
        self.type = "peer"
        self.file = fileName

    def run(self):

        self.client_queue = queue.Queue(20)
        self.handlerSocket = socket.socket()
        self.handlerSocket.connect((self.host,self.port))
        self.rthread = readerThread("ReaderThread", self.handlerSocket, self.host, self.client_queue)
        self.rthread.start()
        self.client_queue.put("USR " + str(my_uuid) + "," + self.host + "," + str(PORT) + "," + self.type)
        time.sleep(4)
        self.client_queue.put("SRC " + self.file)
        time.sleep(6)
        self.sthread = senderThread("SenderThread", self.handlerSocket, self.host,  self.client_queue)
        self.sthread.start()

class Ui_MainWindow (object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.Connect = QtWidgets.QPushButton(self.centralwidget)
        self.Connect.setGeometry(QtCore.QRect(330, 110, 89, 25))
        self.Connect.setObjectName("Connect")
        self.Connect.clicked.connect(self.on_click)

        self.IP = QtWidgets.QLabel(self.centralwidget)
        self.IP.setGeometry(QtCore.QRect(30, 90, 67, 17))
        self.IP.setObjectName("IP")

        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(180, 90, 67, 17))
        self.label_2.setObjectName("label_2")

        self.listWidget = QtWidgets.QListWidget(self.centralwidget)
        self.listWidget.setGeometry(QtCore.QRect(300, 280, 256, 192))
        self.listWidget.setObjectName("listWidget")

        self.lineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit.setGeometry(QtCore.QRect(30, 110, 113, 25))
        self.lineEdit.setObjectName("lineEdit")

        self.lineEdit_2 = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_2.setGeometry(QtCore.QRect(180, 110, 113, 25))
        self.lineEdit_2.setObjectName("lineEdit_2")

        self.lineEdit_3 = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_3.setGeometry(QtCore.QRect(30, 180, 113, 25))
        self.lineEdit_3.setObjectName("lineEdit_3")

        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(30, 160, 67, 17))
        self.label.setObjectName("label")

        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(180, 180, 89, 25))
        self.pushButton.setObjectName("pushButton")
        self.pushButton.clicked.connect(self.click_search)

        self.pushButton_2 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_2.setGeometry(QtCore.QRect(180, 220, 89, 25))
        self.pushButton_2.setObjectName("pushButton_2")
        self.pushButton_2.clicked.connect(self.click)

        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setGeometry(QtCore.QRect(320, 200, 118, 23))
        self.progressBar.setProperty("value", 24)
        self.progressBar.setObjectName("progressBar")
        MainWindow.setCentralWidget(self.centralwidget)

        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")

        MainWindow.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.Connect.setText(_translate("MainWindow", "Connect"))
        self.IP.setText(_translate("MainWindow", "IP"))
        self.label_2.setText(_translate("MainWindow", "PORT"))
        self.label.setText(_translate("MainWindow", "File Name"))
        self.pushButton.setText(_translate("MainWindow", "Search"))
        self.pushButton_2.setText(_translate("MainWindow", "List"))

    @pyqtSlot()
    def on_click(self):
        self.host = self.lineEdit.text()
        print(self.host)
        self.port = self.lineEdit_2.text()
        print(self.port)
        self.type = "peer"
        self.senderQueue = queue.Queue(20)
        self.handlerSocket = socket.socket()
        self.handlerSocket.connect((self.host, int(self.port)))
        self.senderQueue.put("USR " + str(my_uuid) + "," + self.host + "," + str(PORT) + "," +self.type)
        self.rthread = readerThread("ReaderThread", self.handlerSocket, self.host, self.senderQueue)
        self.rthread.start()
        self.sthread = senderThread("SenderThread", self.handlerSocket, self.host, self.senderQueue)
        self.sthread.start()

    @pyqtSlot()
    def click_search(self):
        global file_dict
        for key in file_dict.keys():
            print(file_dict.values())
            print(file_dict.keys())

    @pyqtSlot()
    def click(self):
        self.fileName = self.lineEdit_3.text()
        self.senderQueue.put("LSQ")

        self.rthread = readerThread("ReaderThread", self.handlerSocket, self.host, self.senderQueue)
        self.rthread.start()

        self.sthread = senderThread("SenderThread", self.handlerSocket, self.host, self.senderQueue)
        self.sthread.start()
        self.data = self.senderQueue.get()

        # for key in file_dict.keys():
        #     l = list(file_dict.values())
        # self.listWidget.addItems(l)

        k = 0
        for key in self.data.keys():
            ls = list(self.data.values())
            print(ls[k])


            deneme = ls[k].split(" ")
            k = k + 1
            self.soc = socket.socket()
            self.hostd = deneme[1]
            print(self.hostd)

            self.portd = deneme[0]
            print(self.portd)

            self.queue = queue.Queue(20)
            client_hand = clienthandlerThread("client handler", self.hostd, int(self.portd), self.queue, self.fileName)
            client_hand.start()

class MyMainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MyMainWindow, self).__init__()
        self.setupUi(self)


if __name__ == "__main__":
    import sys

    serv_thr = server_starter()
    serv_thr.start()
    app = QtWidgets.QApplication(sys.argv)
    ui = MyMainWindow()
    ui.show()
    sys.exit(app.exec_())