import logging

import xbmc
import xbmcaddon
import xbmcgui
import json
import urllib
import time
import datetime
import threading

# from threadingimport Thread

addon = xbmcaddon.Addon()
addonname = addon.getAddonInfo('name')

url = "https://www.vrs.de/index.php?eID=tx_vrsinfo_ass2_departuremonitor&i=ea830af655c0cc9dfc7b819d13e5e43f"

clockLabel = xbmcgui.ControlLabel(800, 0, 1000, 500, '', textColor='0xffffffff', font='WeatherTemp')
tformat = "%H:%M:%S"  # "%I:%M:%S:%p"
strActionInfoBoxList = list()
# self.strActionInfo = xbmcgui.ControlLabel(100, 50, 200, 200, '', 'font13', '0xFFFF00FF')

clockThread = 0
threads = []
head_label = head_label = xbmcgui.ControlLabel(50, 0, 600, 100, '', 'font13', '0xFFFFFFFF')

ACTION_PREVIOUS_MENU = 10
ACTION_SELECT_ITEM = 7
ACTION_PARENT_DIR = 9

timetable = list()


class clockThreadClass(threading.Thread):
    def reset(self):
        self.clockLabel = clockLabel
        clockLabel.setText("")

    def stop(self):
        self.shutdown = True

    def run(self):
        self.shutdown = False
        while not self.shutdown:
            if xbmc.abortRequested:
                # log('XBMC abort requested, aborting')
                break
            now = datetime.datetime.now().strftime(tformat)
            clockLabel.setLabel(now)
            time.sleep(0.5)


class timeTableThreadClass(threading.Thread):
    shutdown = False

    def reset(self):
        self.head_label = head_label
        self.timetable = timetable
        self.clockLabel = clockLabel

        clockLabel.setLabel("")
        if len(timetable) == 0:
            logging.ERROR("Timetable has no elements!")
        for row in timetable:
            row[0].setText(" ")
            row[1].setText(" ")
            row[2].setText(" ")
            row[3].setText(" ")
            row[4].setText(" ")

    def update(self):
        self.timetable = timetable
        self.head_label = head_label
        xbmc.log('****** UPDATE TABLE THREAD RUNNING ... ******', xbmc.LOGDEBUG)
        result = json.load(urllib.urlopen(url))
        head_label.setLabel("[B][UPPERCASE][COLOR forestgreen]Abfahrten am Wiener Platz am " + result['updated'] + "[/COLOR][/UPPERCASE][/B]")
        c = 0
        for row in timetable:
            if self.shutdown:
                break
            if len(row) == 0:
                xbmc.log("Timetable has no elements!", xbmc.LOGDEBUG)
                continue
            xbmc.log("Timetable row elemnts: "+str(len(row)), xbmc.LOGDEBUG)
            row[0].setText(" ")
            row[1].setText(" ")
            row[2].setText(" ")
            row[3].setText(" ")
            row[4].setText(" ")
            time.sleep(0.1)
            # estimate
            estimate = ""
            try:
                estimate = " (" + result['events'][c]['departure']['estimate'] + ")"
            except:
                print("NO ESTIMATE")
            row[0].setText(result['events'][c]['departure']['timetable'] + estimate)
            # Typ
            typ = ""
            if result['events'][c]['line']['product'] == "LightRail":
                typ = "Bahn"
            else:
                typ = result['events'][c]['line']['product']
            if not self.shutdown:
                row[1].setText(typ)
            # line
            if not self.shutdown:
                row[2].setText(result['events'][c]['line']['number'])
            # direction
            if not self.shutdown:
                row[3].setText(result['events'][c]['line']['direction'])
            # station
            if not self.shutdown:
                row[4].setText(result['events'][c]['stopPoint']['name'])
            c = c + 1

    def stop(self):
        self.shutdown = True

    def run(self):
        self.shutdown = False
        while not self.shutdown:
            if xbmc.abortRequested:
                # log('XBMC abort requested, aborting')
                break
            for i in range(1, 10):
                if self.shutdown:
                    break
                time.sleep(1)
            if not self.shutdown:
                self.update()


class MyClass(xbmcgui.Window):
    def __init__(self):
        self.retval = 0

        now = datetime.datetime.now().strftime(tformat)

        self.clockLabel = clockLabel
        self.addControl(self.clockLabel)
        self.clockLabel.setLabel(now)

        # Start clock reading thread
        self.clockThread = clockThreadClass()
        self.clockThread.start()

        clockThread = self.clockThread

        self.readjson()

        # Start timetable update thread
        self.timeTableThread = timeTableThreadClass()
        self.timeTableThread.start()
        threads.append(self.timeTableThread)

        self.strActionInfo = xbmcgui.ControlLabel(100, 50, 200, 200, '', 'font13', '0xFFFF00FF')
        self.addControl(self.strActionInfo)
        self.strActionInfo.setLabel('OK to exit!')

        # Headline
        self.strActionInfoBox = xbmcgui.ControlTextBox(50, 100, 600, 100, 'font15', '0xFFFFFFFA')
        head_row = list()
        head_row.append(self.strActionInfoBox)
        self.addControl(self.strActionInfoBox)
        self.strActionInfoBox.setText("[B]Abfahrt[/B]")

        self.strActionInfoBox = xbmcgui.ControlTextBox(200, 100, 600, 100, 'font15', '0xFFFFFFFA')
        head_row.append(self.strActionInfoBox)
        self.addControl(self.strActionInfoBox)
        self.strActionInfoBox.setText("[B]Typ[/B]")

        self.strActionInfoBox = xbmcgui.ControlTextBox(300, 100, 600, 100, 'font15', '0xFFFFFFFA')
        head_row.append(self.strActionInfoBox)
        self.addControl(self.strActionInfoBox)
        self.strActionInfoBox.setText("[B]Linie[/B]")

        self.strActionInfoBox = xbmcgui.ControlTextBox(400, 100, 600, 100, 'font15', '0xFFFFFFFA')
        head_row.append(self.strActionInfoBox)
        self.addControl(self.strActionInfoBox)
        self.strActionInfoBox.setText("[B]Richtung[/B]")

        self.strActionInfoBox = xbmcgui.ControlTextBox(850, 100, 600, 100, 'font15', '0xFFFFFFFA')
        head_row.append(self.strActionInfoBox)
        self.addControl(self.strActionInfoBox)
        self.strActionInfoBox.setText("[B]Haltestelle[/B]")

    def readjson(self):

        uhrzeitx = 50
        tx = 200
        liniex = 300
        richtungx = 400
        haltestellex = 850

        elements = list()

        y = 100
        c = 0

        try:
            result = json.load(urllib.urlopen(url))
            # time.sleep( 5 )

            # head_label = xbmcgui.ControlLabel(50, 0, 600, 100, '', 'font13', '0xFFFFFFFF')
            self.addControl(head_label)
            head_label.setLabel("[B][UPPERCASE][COLOR forestgreen]Abfahrten am Wiener Platz am " + result['updated'] + "[/COLOR][/UPPERCASE][/B]")
            timerow = list()

            timetable.append(timerow)

            y = y + 25
            for event in result['events']:
                timerow = list()
                # print "EVENT LEN:"
                # print len(result['events'])
                maxcount = len(result['events']) - 1
                if c == 30 or c == maxcount:
                    break

                estimate = ""
                try:
                    estimate = " (" + result['events'][c]['departure']['estimate'] + ")"
                except:
                    print("NO ESTIMATE")

                self.strActionInfoBox = xbmcgui.ControlTextBox(uhrzeitx, y, 600, 100, 'font15', '0xFFFFFFFA')
                timerow.append(self.strActionInfoBox)
                self.addControl(self.strActionInfoBox)
                self.strActionInfoBox.setText(result['events'][c]['departure']['timetable'] + estimate)

                # Typ
                typ = ""
                if result['events'][c]['line']['product'] == "LightRail":
                    typ = "Bahn"
                else:
                    typ = result['events'][c]['line']['product']

                self.strActionInfoBox = xbmcgui.ControlTextBox(tx, y, 600, 100, 'font13', '0xFFFFFFFA')
                timerow.append(self.strActionInfoBox)
                self.addControl(self.strActionInfoBox)
                self.strActionInfoBox.setText(typ)
                # self.strActionInfoBox.setText("xxx")

                # Linie
                self.strActionInfoBox = xbmcgui.ControlTextBox(liniex, y, 600, 200, 'font13', '0xFFFFFFFA')
                timerow.append(self.strActionInfoBox)
                self.addControl(self.strActionInfoBox)
                self.strActionInfoBox.setText(result['events'][c]['line']['number'])

                # Richtung
                self.strActionInfoBox = xbmcgui.ControlTextBox(richtungx, y, 600, 100, 'font13', '0xFFFFFFFA')
                timerow.append(self.strActionInfoBox)
                self.addControl(self.strActionInfoBox)
                self.strActionInfoBox.setText(result['events'][c]['line']['direction'])

                # Haltestelle
                self.strActionInfoBox = xbmcgui.ControlTextBox(haltestellex, y, 600, 100, 'font13', '0xFFFFFFFA')
                timerow.append(self.strActionInfoBox)
                self.addControl(self.strActionInfoBox)
                self.strActionInfoBox.setText(result['events'][c]['stopPoint']['name'])
                y = y + 20
                c = c + 1
                timetable.append(timerow)
        except:
            print("ERROR parsing json!")

    def onAction(self, action):
        if action == ACTION_PREVIOUS_MENU:
            # Tell the threads they can stop
            for t in threads:
                t.stop()
                t.reset()
            self.close()
        if action == ACTION_SELECT_ITEM:
            # Tell the threads they can stop
            for t in threads:
                t.stop()
                t.reset()
            self.close()

    def message(self):
        dialog = xbmcgui.Dialog()
        dialog.ok(" My message title", " This is a nice message: " + str(len(timetable)))


mydisplay = MyClass()
mydisplay.doModal()
#mydisplay.show()
del mydisplay
