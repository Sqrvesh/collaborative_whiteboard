import threading
import socket
import pickle

server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server.bind(('localhost',8080))
server.listen()

clients = []
clientno = 0

def handleClient(conn,client):
    global clients
    
    while True:
        try:
            data = pickle.loads(conn.recv(5000))
            if data:
                for i in range(len(clients)):
                    if i!=client:
                        clients[i].extend(data)
            

            conn.send(pickle.dumps(clients[client]))
            clients[client] = []

        except Exception as e:
            conn.close()
            clients[client] = []
            print(e)
            break


while True:
    
    conn,addr = server.accept()
    thread = threading.Thread(target=handleClient,args=(conn,clientno))
    thread.start()
    clientno+=1
    clients.append([])
