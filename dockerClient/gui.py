from ScrolledText import ScrolledText
from tkMessageBox import *
from Tkinter import *
import tkFont
from PIL import ImageTk, Image
import threading
import platform
import client
from time import sleep
import os
import re
from helper import *


class GUI:
    """docstring for GUI"""
##########################################################################
# INIT
##########################################################################

    def __init__(self, app):
        self.stickers = []
        self.preloadStickers = threading.Thread(target=lambda: self.showStickers(preload=True))
        self.preloadStickers.start()

        self.app = app
        app.title("chatS")

        self.images = []
        self.tmp = {'current': ''}
        self.stickersWindowIsOpen = False

        if platform.system() == 'Darwin':
            self.boldfont = tkFont.Font(family='Courier New',
                                    size=20, weight='bold')
            self.mainfont = tkFont.Font(family='Courier New', size=14)
            self.smallfont = tkFont.Font(family='Courier New', size=12)
        else:
            self.boldfont = tkFont.Font(family='Courier New',
                                        size=20, weight='bold')
            self.mainfont = tkFont.Font(family='Courier New', size=10)
            self.smallfont = tkFont.Font(family='Courier New', size=8)

        self.lightGray = '#%02x%02x%02x' % (242, 242, 242)
        self.lightBlue = '#%02x%02x%02x' % (98, 181, 197)

        self.client = client.Client()

        self.receive = threading.Thread(target=self.waitForUpdates)
        self.receive.start()

        self.geometrySetup()
        self.showLoginWindow()

        if not self.client.connectionEstablished:
            showinfo("Connection Failed", "Perhaps, server is not running at the time")
            os._exit(0)

        app.bind("<Escape>", self.quit)

##########################################################################
# GEOMETRY
##########################################################################

    def geometrySetup(self):
        screen_height = app.winfo_screenheight()
        screen_width = app.winfo_screenwidth()
        dim = 600
        x = (screen_width / 2 - dim) / 2
        y = (screen_height - 600) / 2
        app.geometry("%dx%d+%d+%d" % (dim, dim, x, y))
        app.resizable(False, False)

        if platform.system() == 'Darwin':
            os.system('''/usr/bin/osascript -e 'tell app "Finder" to set \
                      frontmost of process "Python" to true' ''')

##########################################################################
# LOGIN WINDOW
##########################################################################

    def showLoginWindow(self):
        self.clearFrame()
        mainCanvas = Canvas(app, width=610, height=610)
        wp = ImageTk.PhotoImage(Image.open("./home/images/login.png"))
        mainCanvas.create_image(610, 610, image=wp, anchor='se')
        self.images.append(wp)
        mainCanvas.place(x=-5, y=-5)

        username = Entry(app, justify='center', bg=self.lightGray,
                         bd=0, exportselection=0, highlightthickness=0,
                         selectbackground=self.lightBlue, font=self.boldfont)
        username.place(anchor='center', width=150, relx=.5, rely=.45)
        username.insert(0, "username")
        username.focus_set()

        password = Entry(app, justify='center', bg=self.lightGray, show='*',
                         bd=0, exportselection=0, highlightthickness=0,
                         selectbackground=self.lightBlue, font=self.boldfont)
        password.place(anchor='center', width=150, relx=.5, rely=.55)
        password.insert(0, "login")

        username.bind("<Return>", lambda event: self.logIn(
            event, username.get(), password.get()))
        password.bind("<Return>", lambda event: self.logIn(
            event, username.get(), password.get()))

        titlefont = tkFont.Font(family='Courier New',
                                size=80, weight='bold')
        mainCanvas.create_text(300, 90, text='chatS', width=500,
                               justify='center', fill='#000000',
                               font=titlefont)

        text = Label(app, text='New to chatS?', bg=self.lightBlue,
                     font=self.smallfont)
        text.place(anchor='center', x=300, y=570)
        text.bind("<Button-1>", self.showInfo)

##########################################################################
# SHOW INFO
##########################################################################

    def showInfo(self, event):
        widget = event.widget
        if widget['text'] == 'New to chatS?':
            notify = threading.Thread(
                    target=lambda: self.notify("New to chatS?", "Enter new username and password and hit enter", 
                                               anchor='n', x=300, ystart=600, yend=550, width=400, crop=False, wait=10))
            notify.start()
        elif widget['text'] == '?':
            notify = threading.Thread(
                    target=lambda: self.notify("New to chatS?", "Click '+' to add new user, '-' to remove existing one.\nReturn to send message, Shift+Return newline",
                                            crop=False, wait=10))
            notify.start()
        elif widget['text'] == '$':
            notify = threading.Thread(
                    target=lambda: self.notify("Like chatS?", 
                                               "Rate it 100 on Moodle!",
                                               wait=5))
            notify.start()

##########################################################################
# LOGIN
##########################################################################

    def logIn(self, event, usr, pwd):
        if self.checkEntryIsDumb(usr, 'username'):
            return

        if self.checkEntryIsDumb(pwd, 'password', minLength=5,
                                 file='./home/validation/dumb_passwords.txt'):
            return

        logInSuccess = self.client.logIn(usr, pwd)

        if logInSuccess:
            self.showMainWindow()
            app.title("chatS - %s" % self.client.username)
        else:
            notify = threading.Thread(
                    target=lambda: self.notify("Log In Failed", "It may happen due to invalid username/password or bad connection.\nOtherwise, it is our fault and we are already working on it!", 
                                               anchor='n', x=300, ystart=600, yend=550, width=500, crop=False, wait=10))
            notify.start()

##########################################################################
# USERNAME & PASSWORD VALIDATION
##########################################################################

    def checkEntryIsDumb(self, entry, entryname, minLength=3,
                         file='./home/validation/swearWords.txt'):
        if re.search('\W', entry):
            notify = threading.Thread(
                    target=lambda: self.notify("Login Failed", "Please use only letters\n and digits for %s" % entryname,
                                               anchor='n', x=300, ystart=600, yend=550, width=500))
            notify.start()
            return True

        if len(entry) < minLength:
            notify = threading.Thread(
                    target=lambda: self.notify("Login Failed", "Please pick longer %s" % entryname,
                                               anchor='n', x=300, ystart=600, yend=550, width=500))
            notify.start()
            return True

        if entryname == 'username' and len(entry) > 21:
            notify = threading.Thread(
                    target=lambda: self.notify("Login Failed", "Please pick shorter %s" % entryname,
                                               anchor='n', x=300, ystart=600, yend=550, width=500))
            notify.start()
            return True

        with open(file) as f:
            dumb = f.read().split()
            if entry.lower() in dumb:
                notify = threading.Thread(
                    target=lambda: self.notify("Login Failed", "Please pick proper %s" % entryname,
                                               anchor='n', x=300, ystart=600, yend=550, width=500))
                notify.start()
                return True
            else:
                return False

##########################################################################
# LOGOUT
##########################################################################

    def logOut(self):
        self.client.logOut()

##########################################################################
# MAIN WINDOW
##########################################################################

    def showMainWindow(self):
        self.clearFrame()
        mainCanvas = Canvas(app, width=610, height=610, bg=self.lightGray)
        mainCanvas.place(x=-5, y=-5)

        scrollbar = Scrollbar(app, width=200)
        self.listbox = Listbox(app, yscrollcommand=scrollbar.set, borderwidth=0,
                         bg=self.lightBlue, fg='#000000',
                         selectbackground=self.lightGray, selectborderwidth=0,
                         font=self.mainfont)

        for k in self.client.friends:
            self.listbox.insert(END, " %s" % k)

        scrollbar.place(x=0, y=0, height=550)
        self.listbox.place(x=0, y=0, width=185, height=550)
        scrollbar.config(command=self.listbox.yview)

        self.listbox.bind('<<ListboxSelect>>', self.listboxSelect)

        text = Label(app, text='+', bg=self.lightBlue,
                     font=self.boldfont)
        text.place(anchor='center', x=25, y=576, width=50, height=49)
        text.bind("<Button-1>", lambda event: threading.Thread(target=lambda: self.notify('', '', bind='addFriend',wait=30)).start())

        text = Label(app, text='-', bg=self.lightBlue,
                     font=self.boldfont)
        text.place(anchor='center', x=75, y=576, width=49, height=49)
        text.bind("<Button-1>", self.deleteFriend)

        text = Label(app, text='?', bg=self.lightBlue,
                     font=self.boldfont)
        text.place(anchor='center', x=125, y=576, width=49, height=49)
        text.bind("<Button-1>", self.showInfo)

        text = Label(app, text='$', bg=self.lightBlue,
                     font=self.boldfont)
        text.place(anchor='center', x=175, y=576, width=49, height=49)
        text.bind("<Button-1>", self.showInfo)

        updates = threading.Thread(target=self.waitForUpdates)
        updates.start()

##########################################################################
# USER SELECTED FRIEND
##########################################################################

    def listboxSelect(self, event):
        try:
            widget = event.widget
            selection = widget.curselection()
            name = widget.get(selection[0]).strip()

            self.updateChatWindow(name)
        except:
            pass

##########################################################################
# DELETE FRIEND
##########################################################################

    def deleteFriend(self, event):
        selection = self.listbox.curselection()
        if len(selection) == 0:
            notify = threading.Thread(
                    target=lambda: self.notify('Delete User', 'Choose user you want to delete',
                                            crop=False, wait=5))
            notify.start()
        else:
            name = self.listbox.get(selection[0]).strip()
            notify = threading.Thread(
                    target=lambda: self.notify('Delete User', name, wait=10,
                                               bind='deleteFriend'))
            notify.start()

##########################################################################
# ADD FRIEND
##########################################################################

    def addFriend(self, name):
        if name in self.client.friends:
            threading.Thread(target=lambda: self.notify('Already Your Friend', name)).start()
            return

        success = self.client.addFriend(name)
        if success == True:
            self.client.friends[name] = []
            self.showMainWindow()
            self.updateChatWindow(name)
        else:
            threading.Thread(target=lambda: self.notify('Unknown User', name)).start()
        return 'break'

##########################################################################
# WAIT FOR UPDATES
##########################################################################

    def waitForUpdates(self):
        while True:
            data = self.client.waitForMessages()

            if self.client.forceDisconnect[0]:
                self.client.saveData()
                showinfo("GoodBye", self.client.forceDisconnect[1])
                os._exit(0)

            if data:
                sentBy, msg = data

                if not sentBy in self.client.friends:
                    self.client.friends[sentBy] = []

                self.client.friends[sentBy].append({'time': time(),
                                                    'sentBy': sentBy,
                                                    'message': msg,
                                                    'status': ''})

                if self.tmp['current'] == '':
                    self.showMainWindow()
                elif self.tmp['current'] == sentBy:
                    self.updateChatWindow(sentBy)
                    continue
                else:
                    text = self.userInput.get(1.0, END)
                    self.showMainWindow()
                    self.updateChatWindow(self.tmp['current'], text)

                notify = threading.Thread(
                    target=lambda: self.notify(sentBy, msg, bind='goToUser'))
                notify.start()

##########################################################################
# NOTIFY
##########################################################################

    def notify(self, sentBy, msg, x=400, ystart=0, yend=50, width=400,
                height=50, anchor='s', bind='', wait=5, crop=True):
        if crop:
            showMsg = msg if len(msg) < 55 else msg[:52]+'...'
        else:
            showMsg = msg

        if bind == '':
            text = Label(app, text="%s\n%s" % (sentBy, showMsg), 
                     bg=self.lightBlue, font=self.smallfont, width=width)
        
        elif bind == 'goToUser':
            text = Label(app, text="%s\n%s" % (sentBy, showMsg), 
                     bg=self.lightBlue, font=self.smallfont, width=width)
            text.bind("<Button-1>", lambda event: self.updateChatWindow(sentBy))
        
        elif bind == 'deleteFriend':
            text = Label(app, text="%s %s ?\n" % (sentBy, msg), 
                     bg=self.lightBlue, font=self.smallfont, width=width)

            noLabel = Label(text, text="NO", bg=self.lightBlue,
                         font=self.mainfont)
            noLabel.place(relx=.4,rely=.8,anchor='c',width=50,height=20)
            noLabel.bind('<Button-1>', lambda e: closeNotification())

            yesLabel = Label(text, text="YES", bg=self.lightBlue,
                         font=self.mainfont)
            yesLabel.place(relx=.6,rely=.8,anchor='c',width=50,height=20)
            yesLabel.bind('<Button-1>', lambda e: yesDeleteFriend())

            def yesDeleteFriend():
                self.client.friends.pop(msg)
                self.tmp['current'] = ''
                self.showMainWindow()
                text.destroy()
                return

        elif bind == 'addFriend':
            text = Label(app, text="Enter Username\n\n", 
                     bg=self.lightBlue, font=self.smallfont, width=width)

            username = Entry(text, justify='center', bg=self.lightGray,
                         bd=0, exportselection=0, highlightthickness=0,
                         selectbackground=self.lightBlue, font=self.mainfont)
            username.place(relx=.5,rely=.65,anchor='c',width=200,height=25)
            username.bind('<Return>', lambda e: self.addFriend(username.get().strip()))
            username.focus_set()

            cancelLabel = Label(text, text="cancel", bg=self.lightBlue,
                         font=self.mainfont)
            cancelLabel.place(relx=.1,rely=.65,anchor='c',width=50,height=20)
            cancelLabel.bind('<Button-1>', lambda e: closeNotification())

            okLabel = Label(text, text="ok", bg=self.lightBlue,
                         font=self.mainfont)
            okLabel.place(relx=.9,rely=.65,anchor='c',width=50,height=20)
            okLabel.bind('<Button-1>', lambda e: self.addFriend(username.get().strip()))

        n = 100.
        y = ystart
        step = (yend - ystart) / n

        while n:
            sleep(0.001)
            n -= 1
            y += step
            try:
                text.place(anchor=anchor, x=x, y=y, width=width, height=50)                
            except:
                continue

        def removeNotification(n, y):
            while n:
                sleep(0.001)
                n -= 1
                y -= step
                try:
                    text.place(anchor=anchor, x=x, y=y, width=width, height=50)
                except:
                    continue

        def closeNotification():
                removeNotification(100, y)
                text.destroy()
                return

        sleep(wait)
        removeNotification(100, y)
        
        text.destroy()

##########################################################################
# UPDATE CHAT WINDOW ON SELECT
##########################################################################

    def updateChatWindow(self, name, entryText=''):
        self.tmp["current"] = name

        chatWindow = ScrolledText(app, undo=True, highlightthickness=0,
                                  font=self.smallfont, bg=self.lightGray)

        messages = self.client.friends[name]
        messagesSorted = sorted(messages, key=lambda m: m['time'])
        windowWidth = 54

        for i, m in enumerate(messagesSorted):
            header = "%s    %s" % (m['time'], m['sentBy'])
            headerLength = len(header)
            statusString = "-"*(headerLength-1)+m['status']
            endingString = "-"*headerLength

            message = m['message']
            if message.startswith("@@@sticker"):
                try:
                    sticker = message.split(':')[1]
                    if len(sticker) > 0:
                        sticker = './home/stickers/%s' % sticker
                        wp = ImageTk.PhotoImage(Image.open(sticker).resize((200, 200)))
                        self.images.append(wp)

                        if m['sentBy'] == self.client.username:
                            message = "\n{:>54}\n{:>54}\n{:>54}\n".format(
                                statusString, header, endingString)
                        else:
                            message = "\n{}\n{}\n{}\n".format(
                                endingString, header, endingString)
                        chatWindow.insert(END, message)

                        padding = 180 if m['sentBy'] == self.client.username else 0
                        chatWindow.image_create(END, image=wp, padx=padding)
                        chatWindow.insert(END, '\n')
                        continue
                except:
                    pass

            if m['sentBy'] == self.client.username:
                message = "\n{:>54}\n{:>54}\n{:>54}\n{:>54}\n".format(
                    statusString, header, endingString, message)
            else:
                message = "\n{}\n{}\n{}\n{}\n".format(
                    endingString, header, endingString, message)
            
            chatWindow.insert(END, message)


        chatWindow.place(x=200, y=0, width=400, height=550)
        # chatWindow.see(END)
        chatWindow.yview(END)
        chatWindow.configure(state=DISABLED)

        self.userInput = ScrolledText(app, undo=True, highlightthickness=0,
                         selectbackground=self.lightBlue, font=self.mainfont)
        if entryText != '':
            self.userInput.insert(END, entryText)

        self.userInput.place(x=250, y=550, width=350, height=50)
        self.userInput.bind("<Return>", self.sendMessage)
        self.userInput.bind("<Shift-Return>", lambda e: self.userInput.insert(END, ""))
        self.userInput.focus_set()

        text = Label(app, text='@', bg='white',
                     font=self.boldfont, anchor=CENTER)
        text.place(anchor='center', x=225, y=576, width=49, height=50)
        text.bind("<Button-1>", lambda e: threading.Thread(target=self.showStickers).start())

##########################################################################
# STICKERS WINDOW
##########################################################################

    def showStickers(self, preload=False):
        if preload:
            for sticker in os.listdir('./home/stickers/'):
                try:
                    img = ImageTk.PhotoImage(Image.open('./home/stickers/'+sticker).resize((92,92)))
                    self.stickers.append([sticker, img])
                except Exception, e:
                    pass

            return

        if self.stickersWindowIsOpen:
            self.stickersWindow.destroy()
            self.stickersWindowIsOpen = False
        else:
            self.stickersWindow = Canvas(app, bg=self.lightGray)
            self.stickersWindow.place(anchor='sw', x=200,y=550,height=288,width=385)

            k = 0
            for sticker, img in self.stickers:
                label = Label(self.stickersWindow, image=img, text=sticker)
                label.grid(row=k / 4, column=k % 4)
                label.bind('<Button-1>', lambda e: threading.Thread(target=lambda: self.sendMessage(e)).start())
                k += 1

            self.stickersWindowIsOpen = True

##########################################################################
# SEND MESSAGE
##########################################################################

    def sendMessage(self, event):
        if self.stickersWindowIsOpen:
            self.stickersWindow.place_forget()
            self.stickersWindowIsOpen = False
            label = event.widget
            msg = "@@@sticker:%s" % label['text']
        else:
            msg = self.userInput.get(1.0, END).strip()

        rcpt = self.tmp['current']

        self.client.sendMessage(rcpt, msg)
        status = 'V' if self.client.messageDelivered else 'X'

        self.client.friends[rcpt].append({'time': time(),
                                          'sentBy': self.client.username,
                                          'message': msg,
                                          'status': status})
        self.updateChatWindow(rcpt)
        return 'break'

##########################################################################
# CLEAR FRAME
##########################################################################

    def clearFrame(self):
        for widget in app.winfo_children():
            widget.destroy()

##########################################################################
# QUICK SHORTCUT HANDLERS
##########################################################################

    def quit(self, event):
        self.client.saveData()
        app.quit()

##########################################################################
# MAIN
##########################################################################

if __name__ == '__main__':
    app = Tk()
    gui = GUI(app)
    app.mainloop()
    gui.logOut()
    os._exit(0)
