import threading
import queue
import socket
import time
import os

my_uuid= os.popen("wmic diskdrive get serialnumber").read().split()[-1]                    #sunucunun uuid'si tutuluyor.(harddisk'e göre)


class LoggerThread(threading.Thread):                                                      # Aptal Sunucunun log dosyasını tutmak için oluşturulmuş
    def __init__(self, name, logQueue, AptalSunucuLog):                                    # Thread'dir. log_server.txt dosyasının içine yazar.
        threading.Thread.__init__(self)
        self.name = name
        self.lQueue = logQueue
        self.fid = open(AptalSunucuLog, "a+")

    def log(self, message):
        t = time.ctime()
        print (t + ":" + message)
        self.fid.write(t + ":" + message + "\n")
        self.fid.flush()

    def run(self):
        self.log("Starting " + self.name)
        while True:
            if not self.lQueue.empty():
                to_be_logged = self.lQueue.get()
                self.log(to_be_logged)


class ReaderThread(threading.Thread):
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
            if msg == "QUI":                                                                # Çıkış işlemi geldiyse soketi de kapatıp çıkar.
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
                self.uuid, self.type = data[4:].split(",")
                self.ip_buffer, self.port_buffer  = str(addr[0:]).split(",")
                self.ip = self.ip_buffer[2:-1]
                self.port = self.port_buffer[1:-1]
                self.timestamp = time.ctime()

                if len(data) < 4:                                                       #ip,port ve type bilgilerini kesin verdi mi kontrolü yapılmalı.
                    self.logQueue.put("Error because of lenght")
                    msg = "ERR"
                    return msg


                if len(self.ip) < 7:                                                    # 0.0.0.0 minimum 7 karakterden oluşur gibi basit bir şey düşündüm,
                    self.logQueue.put("IP bilgisi yanlış")                              # geliştirilmeye açık..
                    msg = "ERR"
                    return msg

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
                    fihrist[self.uuid] = self.ip +" " + self.port + " " + self.type + " " + self.timestamp
                    # print(fihrist)
                    dosya_index.write(str(fihrist)+"\n")                              #giriş yapanları yazıyorum.
                    dosya_index.flush()
                    msg = "HEL " + self.uuid +" " + self.type +" " + self.timestamp   #timestamp ne düşünerek yazmıştık? (TIC gelince timestamp güncellenebilir belki de)
                    return msg

            if data[0:3] == "TIC":                                                    #kendi uuidsini eklesin
                self.logQueue.put(self.uuid + " said TIC")
                msg = "TOC " + my_uuid
                return msg

            if data[0:3] == "LSQ":
                response = ""
                for i in self.fihrist.keys():
                    response += "\n" + i + " " + self.fihrist[i]
                response_list = str(response)
                self.logQueue.put(self.uuid+ " wants to know online user"+ response_list[1:])
                msg = "LSA " + response_list[1:]
                return msg

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

dosya_index = open('index.txt','a')             # sunucuya kimler bağlanmış onun listesini tutacağımız dosya
fihrist = dict()
threads = []

# logger thread
lQueue = queue.Queue(30)
lThread = LoggerThread("Logger Thread", lQueue, "log_server.txt")
lThread.start()
threads.append(lThread)



# Socket dinlenmeye başlanır
s = socket.socket()
host = "0.0.0.0"
port = 12345
s.bind((host,port))
s.listen(5)

rCounter = 1
while True:
    c, addr = s.accept()
    lQueue.put('Got new connection from' + str(addr))
    sendQueue = queue.Queue(10)
    readerThread = ReaderThread("Reader Thread - "+ str(rCounter),
                                c, fihrist, sendQueue,
                                lQueue)
    readerThread.start()
    threads.append(readerThread)
    rCounter += 1

