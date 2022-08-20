# 
# hkQuat (HotKey QUick Access Tool / Thingy)
# ===========================================
# A simple tool for quick access to your preconfigured programs.
#
# Usage:
# - Press the hotkey, or double click on the systray icon
# - Select the preferred programs using
# 	- Search bar
# 	- Arrow keys
# 	- Enter to activate selection
# 	- Esc key to cancel
#	
# Setup:
# - Requires Python 3
# - Required modules: infi.systray
# - Optional modules: keyboard (see: Hotkey options)
# Example: C:\Program Files\Python310\Scripts\pip.exe install infi.systray keyboard*
#
# Hotkey options:
# hkQuat supports direct hotkey assignment using the Python keyboard module, however with 
# Windows 10 assignments may be lost when e.g. locking your screen. To preserve hotkey 
# functionality a workaround is available by using a local network connection using 
# e.g. a telnet client, initiated from a windows shortcut on your desktop with a hotkey. 
# A hotkey assigned to a desktop shortcut is preserved when locking/unlocking your desktop.
# Install telnet in Windows and create a desktop icon with e.g. the following properties:
# - Target: C:\Windows\System32\cmd.exe /C "C:\Windows\System32\telnet.exe 127.0.0.1 45782"
# - Shortcut Key: Ctrl + Alt + ]
# - Run: Minimized
#
# Website: 
#    https://github.com/JCQ81
#

import os, json
import tkinter as Tkinter
import tkinter.ttk as ttk
from socket import socket
from threading import Thread, Event
from infi.systray import SysTrayIcon
try:
    import keyboard
except:
    pass

# Configuration
window_geometry = [ 370, 183 ]
keyboard_hotkey = 'alt+]'
telnet_act_port = 45782

# Globals
evshow = Event()
evquit = Event()
    
# Classes
class App():
    def __init__(self, master):
        self.master = master        

        self.master.title('HotKey QUick Access Thingy')
        self.master.protocol('WM_DELETE_WINDOW', self.hide)
        self.master.wm_attributes('-toolwindow', True)
        self.master.wm_attributes('-topmost', True)
        self.master.geometry(str(window_geometry[0])+'x'+str(window_geometry[1])+'+'+str(self.master.winfo_screenwidth()-window_geometry[0]-10)+'+'+str(self.master.winfo_screenheight()-window_geometry[1]-65))
        self.master.resizable(False, False)

        self.master.lbquery = Tkinter.Label(self.master, text='Query:')
        self.master.enquery = Tkinter.Entry(self.master, width=50)
        self.master.enquery.bind('<KeyRelease>', self.enquery_onchange_regkeys)
        self.master.enquery.bind('<Return>', lambda _: self.enquery_onchange_spckeys(0x20))
        self.master.enquery.bind('<Escape>', lambda _: self.enquery_onchange_spckeys(0x27))
        self.master.enquery.bind('<Up>',     lambda _: self.enquery_onchange_spckeys(0x48))
        self.master.enquery.bind('<Down>',   lambda _: self.enquery_onchange_spckeys(0x50))
        self.master.lbquery.grid(row=0, column=0, sticky=Tkinter.W)
        self.master.enquery.grid(row=0, column=1, sticky=Tkinter.W)
        self.master.tree = ttk.Treeview(self.master, columns=('name', 'type', 'comm'), displaycolumns=('name', 'type'), show='tree', height=8)
        self.master.tree.column('#0', minwidth=0, width=0, stretch=0)
        self.master.tree.column('name', minwidth=0, width=window_geometry[0]-103, stretch=1)
        self.master.tree.column('type', minwidth=0, width=100, stretch=0)
        self.master.tree.grid(row=1, column=0, columnspan=2)
        self.master.tree.bind('<Return>',   self.tree_onselect)
        self.master.tree.bind('<Double-1>', self.tree_onselect)
        self.master.tree.bind('<Escape>',   self.tree_oncancel)
        self.master.treeview = self.master.tree
        try:
            keyboard.add_hotkey(keyboard_hotkey, self.show)
        except:
            pass

        self.tvitems_detached=[]
        with open('hkQuat.json') as data_file:            
            items = json.load(data_file)['items']
            for key, value in items.items():
                self.master.tree.insert('' ,Tkinter.END, values=[value['name'],value['type'],value['command']])
        self.tree_sort(self.master.tree, 'name', False)        

    def show(self):
        self.master.update()
        self.master.deiconify()

    def hide(self):  
        self.master.withdraw()
        self.master.enquery.delete(0,255)
        self.enquery_onchange_regkeys(0x00)

    def close(self):
        self.master.quit()

    def enquery_onchange_spckeys(self, key):
        select = self.master.tree.get_children()[0]
        if key == 0x20:
            os.system(self.master.tree.item(select)['values'][2])
            self.hide()
        if key == 0x27:
            self.hide()
        if key == 0x48: 
            self.master.tree.focus_set()
            self.master.tree.focus(select)
            self.master.tree.selection_set(select)
        if key == 0x50: 
            self.master.tree.focus_set()
            self.master.tree.focus(select)
            self.master.tree.selection_set(select)
        return True
    
    def enquery_onchange_regkeys(self, key):
        for item in self.tvitems_detached:
            self.master.tree.reattach(item,'',0)
        self.tvitems_detached.clear()
        tvitems=self.master.tree.get_children()
        for item in tvitems:
            if self.master.enquery.get().lower() not in self.master.tree.item(item)['values'][0].lower():
                self.master.tree.detach(item)
                self.tvitems_detached.append(item)
        self.tree_sort(self.master.tree, 'name', False)
        return True

    def tree_onselect(self, event):
        item = self.master.tree.selection()[0]
        os.system(self.master.tree.item(item)['values'][2])
        self.hide()

    def tree_oncancel(self, event):        
        self.hide()

    def tree_sort(self, tv, col, rev):        
        column_index = self.master.tree['columns'].index(col)
        l = [(str(tv.item(k)['values'][column_index]), k) for k in tv.get_children()]
        l.sort(key=lambda t: t[0], reverse=rev)
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)        
        tv.heading(col, command=lambda: self.master.tree_sort(tv, col, not rev))

class SocketServer(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.server = socket()
        self.server.settimeout(1)
        self.server.bind(('127.0.0.1', telnet_act_port))
        self.server.listen()

    def run(self):
        while not evquit.is_set():
            try:          
                client, addr = self.server.accept()
                client.close()
                evshow.set()
            except:                    
                pass

# Main
def main():    
    root = Tkinter.Tk()
    app = App(root)
    app.hide()
    
    def eventhandler():
        if evshow.is_set():
            app.show()
            evshow.clear()
        if evquit.is_set():
            app.close()
        else:
            root.after(100, eventhandler)

    systray = SysTrayIcon('hkQuat.ico', 'hkQuat', (('Show', None, lambda _: evshow.set()),), on_quit=lambda _: evquit.set())
    systray.start()

    socketserver = SocketServer()
    socketserver.start()

    root.after(100, eventhandler)    
    root.mainloop()

if __name__=='__main__':
    main()
