from os import _exit
from socket import *
import threading
from time import sleep
import hashlib
import json
from datetime import datetime

##########################################################################
# ERROR CODES
##########################################################################

msgCodes = {
    -10: 'BLACKLISTED CONNECTION/USER',
    -1: 'ADDED TO BLACKLIST',
    0: 'OK',
    100: 'SERVER FAIL',
    10: 'CLIENT FAIL',
    20: 'UNKNOWN USER',
    200: 'FORCE CLIENT DISCONNECT',
    300: 'LOGIN FAIL',
    400: 'MESSAGE DELIVERY FAIL',
    500: 'KEYBOARD INTERRUPT'
}

##########################################################################
# READ DATA FROM FILE
##########################################################################


def readFromFile(filename):
    try:
        with open(filename) as f:
            data = f.read()
            if len(data) > 0:
                return json.loads(data)
            else:
                return {}
    except:
        open(filename, 'w').close()
        return {}

##########################################################################
# SAVE DATA TO FILE
##########################################################################


def saveToFile(filename, data):
    try:
        with open(filename, 'w') as f:
            f.write(json.dumps(data, default='utf8'))
    except:
        return

##########################################################################
# GET CURRENT DATE & TIME
##########################################################################


def time():
    return datetime.now().strftime("%Y/%m/%d %H:%M")

##########################################################################
# COMPOSE MESSAGE
##########################################################################


def composeMessage(_id, _type, message, status=0):
    msg = {
        'id': _id,
        'type': _type,
        'message': message,
        'status': status
    }

    return json.dumps(msg, default='utf8')
