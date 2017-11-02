from helper import *
from os import _exit
import sys


class Client():
    """docstring for Client"""
##########################################################################
# INIT
##########################################################################

    def __init__(self, server="", port=11111):
        # open('./home/client.log', 'w').close()

        self.log('STARTING CLIENT')

        self.username = ''
        self.loggedIn = False
        self.connectionEstablished = False
        self.waitingForResponse = False
        self.messageDelivered = None
        self.newUserAdded = None
        self.forceDisconnect = [False, '']
        self.friends = {}

        self.connect(server, port)

        # dev = threading.Thread(target=self.developerTools)
        # dev.start()

##########################################################################
# ESTABLISH CONNECTION
##########################################################################

    def connect(self, server="", port=11111):
        try:
            self._socket = socket(AF_INET, SOCK_STREAM)
            self._socket.connect((server, port))

            self.log('CONNECTING')
            self.connectionEstablished = True
        except:
            self.log('CONNECTING', status=10)

##########################################################################
# LOGIN
##########################################################################

    def logIn(self, usr, pwd):
        digest = hashlib.sha256(pwd).hexdigest()
        message = composeMessage('login', 'request',
                                 {'usr': usr, 'pwd': digest},
                                 status=0)
        self._socket.send(message)
        self.waitForResponse()

        if self.loggedIn:
            self.username = usr
            self.friends = readFromFile('./home/data/%s_friends.json' % self.username)

        return self.loggedIn

##########################################################################
# LOGOUT
##########################################################################

    def logOut(self):
        self.loggedIn = False
        message = composeMessage('logout', 'request', '')
        self._socket.send(message)
        self.log("DISCONNECTED")
        self.saveData()

##########################################################################
# DEV TOOLS
##########################################################################

    def developerTools(self):
        while True:
            command = sys.stdin.readline().strip()
            if command == 'q':
                self.logout()
                _exit(0)
            elif command == 'cl':
                open('./home/client.log', 'w').close()

##########################################################################
# LOGGING
##########################################################################

    def log(self, info, status=0):
        self.saveData
        logEntry = "{};{};{};{}".format(time(), info, status, msgCodes[status])
        print logEntry
        with open('./home/client.log', 'a') as f:
            f.write(logEntry+'\n')

##########################################################################
# SAVE ALL DATA
##########################################################################

    def saveData(self):
        if self.loggedIn:
            saveToFile('./home/data/%s_friends.json' % self.username, self.friends)

##########################################################################
# WAIT FOR MESSAGES
##########################################################################

    def waitForMessages(self):
        while True:
            message = self._socket.recv(10000)
            if len(message) > 0:
                try:
                    message = json.loads(message)
                    if message['id'] == 'message':
                        return self.userMessagesHandling(message)
                    else:
                        return self.serviceMessagesHandling(message)
                except:
                    continue
            else:
                pass

##########################################################################
# WAIT FOR RESPONSE
##########################################################################

    def waitForResponse(self):
        self.waitingForResponse = True
        k = 30

        while self.waitingForResponse and k:
            sleep(.1)
            k -= 1

##########################################################################
# SERVICE MESSAGES
##########################################################################

    def serviceMessagesHandling(self, message):
        self.log(message['message'], status=message['status'])
        if message['status'] == 200:
            self.forceDisconnect = [True, message['message']]

        if message['id'] == 'login' and message['type'] == 'response':
            if message['status'] == 0:
                self.loggedIn = True
                self.waitingForResponse = False
            return

        if message['id'] == 'adduser' and message['type'] == 'response':
            if message['status'] == 0:
                self.newUserAdded = True
            else:
                self.newUserAdded = False

            self.waitingForResponse = False
            return

##########################################################################
# USER MESSAGES
##########################################################################

    def userMessagesHandling(self, message):
        if message['type'] == 'response':
            if message['status'] == 0:
                self.messageDelivered = True
            else:
                self.messageDelivered = False

            self.log("MESSAGE DELIVERY TO %s" % message['message']['rcpt'],
                     status=message['status'])
            self.waitingForResponse = False
            return

        if message['type'] == 'receive':
            message = message['message']
            return (message['sentBy'], message['msg'])

##########################################################################
# SEND MESSAGE
##########################################################################

    def sendMessage(self, rcpt, msg):
        self.log("SENDING MESSAGE TO %s" % rcpt)
        self.messageDelivered = None
        message = composeMessage('message', 'send',
                                 {'rcpt': rcpt, 'msg': msg,
                                  'sentBy': self.username})
        self._socket.send(message)
        self.waitForResponse()

        return self.messageDelivered

##########################################################################
# ADD FRIEND
##########################################################################

    def addFriend(self, name):
        self.log("ADDING NEW USER %s" % name)
        self.newUserAdded = None
        message = composeMessage('adduser', 'request',
                                 {'user': name})
        self._socket.send(message)
        self.waitForResponse()

        return self.newUserAdded

##########################################################################
# MAIN
##########################################################################

if __name__ == '__main__':
    client = Client()
