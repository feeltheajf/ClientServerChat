from helper import *
from os import _exit
import signal
import re


class Server():
    """docstring for Server"""
##########################################################################
# INIT
##########################################################################

    def __init__(self, port=11111):
        # open('./home/server.log', 'w').close()

        self.log('STARTING SERVER')

        self.connections = {}
        self.blackIPs = readFromFile('./home/data/blackIPs.json')
        self.blackUsers = readFromFile('./home/data/blackUsers.json')
        self.users = readFromFile('./home/data/users.json')

        self.connect(port)

        dev = threading.Thread(target=self.developerTools)
        dev.start()

        def signalHandler(signal, frame):
            self.saveData()
            self.log("SERVER SHUTDOWN", 500)
            _exit(0)

        signal.signal(signal.SIGINT, signalHandler)

        self.mainloop()

##########################################################################
# ESTABLISH CONNECTION
##########################################################################

    def connect(self, port):
        try:
            self._socket = socket(AF_INET, SOCK_STREAM)
            self._socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

            self._socket.bind(("", port))
            self._socket.listen(5)

            self.log('CONNECTING')
        except:
            self.log('CONNECTING', status=100)
            _exit(0)

##########################################################################
# SERVER MAINLOOP
##########################################################################

    def mainloop(self):
        while True:
            connection, info = self._socket.accept()
            self.connections[info[1]] = [connection, info[0], '']

            if info[0] in self.blackIPs:
                if self.blackIPs[info[0]] > 10:
                    self.forceDisconnect(connection, info[1])
                    self.log("CONNECTION REFUSED {}:{}".format(info[0],info[1]), -10)
                    continue

            self.log("{}:{} CONNECTED".format(info[0], info[1]))

            client = threading.Thread(
                target=self.handleClient, args=(connection, info))
            client.start()

##########################################################################
# DEV TOOLS
##########################################################################

    def developerTools(self):

        def devMan():
            with open('./home/manpage') as f:
                print f.read()

        def devQuit():
            self.log('SERVER SHUTDOWN')
            self.saveData()
            _exit(0)

        def devListClients():
            print '> clients connected:\n' +\
                    '\n'.join(sorted("%-25s%s:%s" % (j[2], j[1], i)
                              for i, j in self.connections.items()))

        def devClearLogs():
            open('./home/server.log', 'w').close()
            print '> logs cleared'

        def devForceDisconnect(clients):
            for client in clients:
                try:
                    client = int(client)
                except:
                    if re.search('\.', client):
                        for i in self.connections:
                            if self.connections[i][1] == client:
                                client = i
                                break
                    else:
                        try:
                            client = self.users[client]['info'][1]
                        except:
                            pass
                try:
                    self.forceDisconnect(self.connections[client][0], client)
                except: 
                    print "INVALID ARGUMENT. PERHAPS, USER IS NOT CONNECTED"

        def devBlack():
            print "> black IPs:"
            print "\n".join(sorted(["{:<25}   {} ({})".format(
                                    ip, self.blackIPs[ip], "x"*self.blackIPs[ip]) for ip in self.blackIPs], 
                        key=lambda x: x.split()[1],reverse=True))

            print "\n> black Users:"
            print "\n".join(sorted(["{:<25}   {} ({})".format(
                                    user, self.blackUsers[user], "x"*self.blackUsers[user]) for user in self.blackUsers], 
                        key=lambda x: x.split()[1],reverse=True))

        knownCommands = {
            'man':  devMan,
            'q':    devQuit,
            'lc':   devListClients,
            'cl':   devClearLogs,          
            'bl':   devBlack
        }

        while True:
            command = raw_input().strip().lower().split()

            if len(command) > 1:
                if command[0] == 'fd':
                    devForceDisconnect(command[1:])
                else:
                    print 'INVALID COMMAND. SEE MAN' 
            else:
                command = command[0]

                if command in knownCommands:
                    knownCommands[command]()
                else:
                    print 'INVALID COMMAND. SEE MAN' 

##########################################################################
# LOGGING
##########################################################################

    def log(self, info, status=0):
        self.saveData
        logEntry = "{};{};{};{}".format(time(), info, status, msgCodes[status])
        print logEntry
        with open('./home/server.log', 'a') as f:
            f.write(logEntry+'\n')

##########################################################################
# SAVE ALL DATA
##########################################################################

    def saveData(self):
        users = {}
        for u,d in self.users.items():
            users[u] = {'pwd': d['pwd']}

        saveToFile('./home/data/users.json', users)
        saveToFile('./home/data/blackIPs.json', self.blackIPs)
        saveToFile('./home/data/blackUsers.json', self.blackUsers)

##########################################################################
# CLIENT HANDLING
##########################################################################

    def handleClient(self, connection, info):
        k = 5
        while k:
            try:
                message = connection.recv(10000)
            except:
                break
            if len(message) > 0:
                try:
                    message = json.loads(message)
                    if message['id'] == 'message':
                        self.userMessagesHandling(
                            message, connection, info=info)
                    else:
                        self.serviceMessagesHandling(
                            message, connection, info=info)
                except:
                    continue
            else:
                k -= 1

        try:
            self.forceDisconnect(connection, info[1])
        except:
            pass

##########################################################################
# FORCE DISCONNECT
##########################################################################

    def forceDisconnect(self, connection, port):
        _, ip, name = self.connections[port]

        if len(name) > 0:
            if name in self.blackUsers:
                self.blackUsers[name] += 1
            else:
                self.blackUsers[name] = 1
                self.log("NEW BADASS {}:{} ({})".format(ip, port, name), -1)

        if ip in self.blackIPs:
            self.blackIPs[ip] += 1
        else:
            self.blackIPs[ip] = 1
            self.log("NEW BADASS {}:{} ({})".format(ip, port, name), -1)


        connection.send(composeMessage('notify', '',
                                       '''YOU WERE FORCE DISCONNECTED \
BY SERVER. IT MAY HAPPEN DUE TO SEVERAL REASONS: LONG IDLE, BLACKLIST, JUST4FUN!''', status=200))
        self.connections.pop(port)
        connection.close()
        self.log("{}:{} ({}) DISCONNECTED".format(ip, port, name), 200)

##########################################################################
# SERVICE MESSAGES
##########################################################################

    def serviceMessagesHandling(self, message, connection, info=''):
        if message['id'] == 'login' and message['type'] == 'request':
            self.loginHandler(message['message'], connection, info=info)
            return

        if message['id'] == 'logout' and message['type'] == 'request':
            self.logoutHandler(connection, info)
            return

        if message['id'] == 'adduser' and message['type'] == 'request':
            usr = message['message']['user']
            if usr in self.users:
                status = 0
            else:
                status = 20

            response = composeMessage('adduser', 'response', 'USER ADDED', status)
            connection.send(response)
            self.log("LOOKING FOR USER %s" % usr, status)

##########################################################################
# HANDLE LOGIN
##########################################################################

    def loginHandler(self, message, connection, info=''):
        usr = message['usr'].lower()
        pwd = message['pwd']

        if usr in self.blackUsers:
            if self.blackUsers[usr] > 10:
                self.forceDisconnect(connection, self.users[usr]['info'][1])
                self.log("LOGIN REFUSED {}:{} ({})".format(info[0],info[1],usr), -10)
                return

        if usr in self.users:
            knownUser = self.users[usr]
            if pwd == knownUser['pwd']:
                knownUser['connection'] = connection
                knownUser['info'] = info
                self.users[usr] = knownUser
                status = 0
                self.connections[info[1]][2] = usr
                self.log("USER LOGGED IN: %s" % usr, status)
            else:
                status = 300
                self.log("USER FAILED TO LOG IN: %s" % usr, status)
        else:
            self.users[usr] = {'connection': connection,
                               'info': info,
                               'pwd': pwd}
            status = 0
            self.connections[info[1]][2] = usr
            self.log('NEW USER: %s' % usr, 0)

        response = composeMessage('login', 'response', "USER LOGIN",
                                  status=status)
        connection.send(response)

##########################################################################
# HANDLE LOGOUT
##########################################################################

    def logoutHandler(self, connection, info):
        try:
            self.connections.pop(info[1])
            self.log("{}:{} DISCONNECTED".format(info[0], info[1]))
            connection.close()
        except:
            pass

##########################################################################
# USER MESSAGES
##########################################################################

    def userMessagesHandling(self, message, connection, info=''):
        if message['type'] == 'send':
            data = message['message']
            rcpt = data['rcpt']
            text = data['msg']
            user = data['sentBy']

            if rcpt in self.users:
                knownRcpt = self.users[rcpt]
                rcptPort = knownRcpt['info'][1]

                if rcptPort in self.connections:
                    rcptConnection = self.connections[rcptPort][0]
                    message = composeMessage('message', 'receive',
                                             {'sentBy': user, 'msg': text})
                    rcptConnection.send(message)
                    status = 0
                    self.log("MESSAGE SENT FROM: %s TO: %s" % (user, rcpt))
                else:
                    status = 400
                    self.log("RCPT OFFLINE: %s" % rcpt, status)
            else:
                status = 400
                self.log("UNKNOWN RCPT FROM: %s TO: %s" % (user, rcpt), status)

            response = composeMessage('message', 'response',
                                      {'user': user, 'rcpt': rcpt},
                                      status=status)
            connection.send(response)

##########################################################################
# MAIN
##########################################################################

if __name__ == '__main__':
    server = Server()
