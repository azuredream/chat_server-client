import argparse
import socket
import select
import sys
import signal
import pickle
import struct

HOST_NAME = socket.gethostname()

class chating_server(object):
    def __init__(self,hostname,port):
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.sock.bind((hostname,port))
        self.sock.listen(5)
        self.input  = [self.sock,sys.stdin]
        self.output = []
        self.client_namemap = {}
        signal.signal(signal.SIGINT,self.sighandler)
        print("server listing to port %s..."%port)

    def sighandler(self,signum,frame):
        print("shutting down server")
        for o in self.output:
            o.close()
        self.sock.close()

    def send(self,sendsock,*args):
        buffer = pickle.dumps(args)
        size = struct.pack("L",socket.htonl(len(buffer)))
        sendsock.send(size)
        sendsock.send(buffer)

    def receive(self,receivesock):
        try:
            size = receivesock.recv(struct.calcsize("L"))
            size = socket.ntohl(struct.unpack("L",size)[0])
        except struct.error as e:
            return ''
        msg = ""
        if len(msg)<size:
            msg += receivesock.recv(size-len(msg))
        return pickle.loads(msg)[0]

    def run(self):
        running = True
        while running:
            readablesock,writeablesock,e = select.select(self.input,self.output,[])
            for sock in readablesock:
                if sock == self.sock:
                    client,address = self.sock.accept()
                    self.input.append(client)
                    self.output.append(client)
                    clientname = self.receive(client).split("NAME: ")[1]
                    self.client_namemap[client] = (address,clientname)
                    msg = "\nclient %s connect!"%clientname
                    for o in self.output:
                        self.send(o,msg)
                elif sock == sys.stdin:
                    #running == False
                    pass
                else:
                    try:
                        #chating
                        data = self.receive(sock)
                        if not data:
                            sock.close()
                            self.input.remove(sock)
                            self.output.remove(sock)
                            msg = "client %s is disconnected"%self.client_namemap[client][1]
                            for o in self.output:
                                self.send(o,"\n%s"%msg)
                        else:
                            for o in self.output:
                                if o !=sock:
                                    self.send(o,"\n%s>>>"%self.client_namemap[sock][1]+data)
                    except socket.error as e:
                        self.output.remove(sock)
                        print("socket error remove %s"%self.client_namemap[sock])
        self.sock.close()
        print("close server")


class chating_client(object):
    def __init__(self,name,host,port):
        self.connect = False
        self.name = name
        try:
            self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.sock.connect((host,port))
            self.connect = True
            print("connect to server!")
            self.send(self.sock,"NAME: "+name)
            data = self.receive(self.sock)
            print("%s"%data)
        except socket.error,e:
            print("connect failed")
            sys.exit(1)
    def send(self,sendsock,*args):
        buffer = pickle.dumps(args)
        size = struct.pack("L",socket.htonl(len(buffer)))
        sendsock.send(size)
        sendsock.send(buffer)

    def receive(self,receivesock):
        try:
            size = receivesock.recv(struct.calcsize("L"))
            size = socket.ntohl(struct.unpack("L",size)[0])
        except struct.error as e:
            return ''
        msg = ""
        if len(msg)<size:
            msg += receivesock.recv(size-len(msg))
        return pickle.loads(msg)[0]
    def run(self):
        while self.connect:
            try:
                sys.stdout.write("%s>>>"%self.name)
                sys.stdout.flush()
                readablesock,writeablesock,e = select.select([0,self.sock],[],[])
                for sock in readablesock:
                    if sock == 0:
                        data = sys.stdin.readline().strip()
                        if data:
                            self.send(self.sock,data)
                    elif sock == self.sock:
                        data = self.receive(self.sock)
                        if data:
                            sys.stdout.write(data+'\n')
                            sys.stdout.flush()
                        else:
                            print("client shutting down")
                            self.connect = False
            except KeyboardInterrupt:
                print("client interrupted")
                self.sock.close()
                break

if __name__ == "__main__":
    parse = argparse.ArgumentParser(description="chatting server and client")
    parse.add_argument('--name',action="store",dest="name",required=True)
    parse.add_argument('--port',action="store",type=int,dest="port",required=True)
    parsedict = parse.parse_args()
    name = parsedict.name
    port = parsedict.port
    if name == "server":
        server = chating_server(HOST_NAME,port)
        server.run()
    else:
        client = chating_client(name,HOST_NAME,port)
        client.run()



















