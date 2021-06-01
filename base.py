# -*- coding: utf-8 -*-
#
# --- Import the libraries
#

from psychopy import core, visual, event, data  # gui, data, misc, sound
from psychopy.hardware import joystick
# import time
# import numpy
# import os.path
import pygame
import copy
import collections
import random
import os.path
import os
import struct

try:
    from ctypes import windll
    par = True
except:
    par = False

try:
    import requests
except:
    requests = False


#
# -- Define clocks
#

globalClock = core.Clock()


#
# -- support functions
#

def amul(list, f):
    list = [e * f for e in list]
    return list


def readDFile(filename, sep=None, enc='utf-8'):
    s = file(filename).readlines()
    s = [l.decode(enc) for l in s]
    if sep is None:
        s = [l.split() for l in s]
    else:
        s = [l.split(sep) for l in s]
    s = [[e.strip() for e in l] for l in s]
    return s


# ---> Joystick

def getJoystick(backend='pygame', joined=False):
    if joined:
        pygame.init()
        pygame.joystick.init()
        joy = pygame.joystick.Joystick(0)
        joy.init()
    else:
        joystick.backend = backend
        nJoys = joystick.getNumJoysticks()
        joy   = joystick.Joystick(nJoys - 1)
    return joy


class Joystick(object):

    def __init__(self, win, backend='pygame', joined=False, start=None, flip=None):

        self.backend = backend
        self.joined  = joined
        self.start   = start
        self.win     = win

        if joined:
            pygame.init()
            pygame.joystick.init()
            self.joy = pygame.joystick.Joystick(0)
            self.joy.init()
            self.backend = 'pygame'
        else:
            joystick.backend = backend
            nJoys = joystick.getNumJoysticks()
            self.joy = joystick.Joystick(nJoys - 1)

        if start is None:
            self.start = (0, 0)

        if flip is None:
            self.flip = 1
        elif flip is True:
            self.flip = -1
        else:
            self.flip = 1


    def getX(self):

        if self.backend == 'pygame':
            return self.joy.get_axis(0)
        else:
            return self.joy.getX

    def getY(self):

        if self.backend == 'pygame':
            return self.joy.get_axis(1)
        else:
            return self.joy.getY

    def getAllButtons(self):
        self.joy.init()
        event.clearEvents()
        if self.backend == 'pygame':
            pygame.event.get()
            buttonsPressed = []
            for i in range(0, self.joy.get_numbuttons()):
                buttonsPressed.append(self.joy.get_button(i))
            # self.joy.quit()
            return buttonsPressed
        else:
            self.joy.quit()
            return self.joy.getAllButtons

    def getXY(self):
        self.joy.init()
        event.clearEvents()
        pygame.event.get()
        # pygame.event.pump()
        x = self.start[0] + (self.getX() * self.win.size[0] // 2) * self.flip
        y = self.start[1] - self.getY()  * self.win.size[1] // 2
        self.joy.quit()

        return (x, y)


# ----> mouse presses

def waitForMouse(mouse, nkeys=1, maxtime=1000, mask=None, clock=None, fulltime=None):

    # mouse = event.Mouse()

    presses = 0
    keys    = []
    times   = []
    if clock is None:
        clock = core.Clock()

    event.clearEvents()
    mouse.clickReset()

    while presses < nkeys and clock.getTime() < maxtime:

        while True:
            try:
                buttons, times = mouse.getPressed(getTime=True)
                if sum(times) > 0:
                    break
            except:
                print(mouse.getPressed(getTime=True))

        presses += 1
        keys.append(times)
        times.append(clock.getTime())
        event.clearEvents()

    if fulltime is not None and clock.getTime() < fulltime:
        core.wait(fulltime - clock.getTime())

    return (keys, times)


# ----> Key presses

def waitForKeys(nkeys=1, maxtime=1000, mask=None, clock=None, fulltime=None):

    presses = 0
    keys    = []
    times   = []
    if clock is None:
        clock = core.Clock()

    while presses < nkeys and clock.getTime() < maxtime:
        allKeys = event.waitKeys(maxWait=maxtime - clock.getTime(), keyList=mask, timeStamped=clock)
        if allKeys is not None:
            for thisKey, thisTime in allKeys:
                presses += 1
                keys.append(thisKey)
                times.append(thisTime)
        event.clearEvents()

    if fulltime is not None and clock.getTime() < fulltime:
        core.wait(fulltime - clock.getTime())

    return (keys, times)



def drawCue(win, text="+"):
    m = visual.TextStim(win, color=[1.0, 1.0, 1.0], pos=[0, 0], height=40, text=text, bold=True, alignHoriz='center', flipHoriz=True)
    m.draw()
    return m



def showInstructions(win, instructions=None):
    """Shows a series of screens with text and durations provided in the instructions [(text, duration)] list of tuples."""

    if instructions is not None:
        for text, duration in instructions:
            drawCue(win, text)
            win.flip()
            if duration > 0:
                core.wait(duration)
            else:
                event.waitKeys()
            win.flip()


#
# --- Cedrus wrapper that selects appropriate library if available
#
class Cedrus(object):
    """A class that selects appropriate interface for communicating with Cedrus equipment."""

    def __init__(self, sync=4, TR=None):
        devCount = 0
        # try connecting via pyxid2
        try:
            import pyxid2.pyxid2 as pyxid2
            scanner = pyxid2.XIDDeviceScanner.GetDeviceScanner()
            scanner.DetectXIDDevices()
            devCount = scanner.DeviceCount()
            if (devCount > 0):
                dev = scanner.DeviceConnectionAtIndex(0)
                self.interface = CedrusXID2(sync, TR, dev)
                self.interfaceType = 'pyxid2'
                print("\nCedrus pyxid2 loaded!\n")
        except:
            print("\nCedrus pyxid2 load failed, trying the ASCII library!\n")

        # try connecting via pyxid
        if (devCount == 0):
            try:
                import pyxid
            except:
                print("\nCedrus pyxid load failed!\n")
                
            for n in range(0, 3):
                try:
                    dev = pyxid.get_xid_devices()[0]
                    self.interface = CedrusASCII(sync, TR, dev)
                    self.interfaceType = 'ASCII'
                    break
                except:
                    if n == 2:
                        print("\nERROR: Could not set up Cedrus response pad!\n")
                        raise

    def waitSync(self, sync=None, clock=None):
        return self.interface.waitSync(sync, clock)

    def waitForKeys(self, nkeys=1, maxtime=1000, mask=None, clock=None, mintime=None, pressed=None, clearcue=None, fulltime=None, callout=None):
        return self.interface.waitForKeys(nkeys, maxtime, mask, clock, mintime, pressed, clearcue, fulltime, callout)
    
    def emptyCue(self):
        self.interface.emptyCue()

    def resetRTTimer(self):
        if (self.interfaceType == 'pyxid2'):
            self.interface.resetRTTimer()

#
# --- Cedrus pyxid2: A version of Cedrus code that uses the new pyxid2 lib
#

class CedrusXID2(object):
    """A class for wrapping cedrus related methods for the new pyxid2 library."""

    def __init__(self, sync=4, TR=None, dev=None, lightSensor=False):
        try:
            if (dev is None):
                import pyxid2.pyxid2 as pyxid2
                scanner = pyxid2.XIDDeviceScanner.GetDeviceScanner()
                scanner.DetectXIDDevices()
                self.dev = scanner.DeviceConnectionAtIndex(0)
            else:
                self.dev = dev

            self.dev.ResetRtTimer()
            self.syncKey = sync
            self.baseClock = core.MonotonicClock()
            self.lightSensor = lightSensor
 
            if lightSensor:
                # input on light sensor resets RT timer
                self.dev.SetTimerResetOnOnsetMode(ord('A'), 1)
                # set default threshold
                self.dev.SetAnalogInputThreshold(ord('A'), 25)
        except:
            print("\nERROR: Could not set up Cedrus response pad!\n")
            raise

        self.TR = TR
        if TR is None:
            self.syncClock = False
        else:
            self.syncClock = core.Clock()


    def waitSync(self, sync=None, clock=None):

        if clock is None:
            clock = core.Clock()

        # --- are we simulating sync?
        if self.TR:
            while int(self.syncClock.getTime() * 100) % int(self.TR * 100):
                pass
            clock.reset()
            return (clock.getTime(), clock)

        # --- empty cue and wait for sync
        print("  --- waiting for sync pulse ---  ")
        self.emptyCue()

        if sync is None:
            sync = self.syncKey

        while True:
            self.dev.PollForResponse()
            while self.dev.HasQueuedResponses():
                time = clock.getTime()
                cedrusResponse = self.dev.GetNextResponse()

                # --- process response
                if cedrusResponse.key == sync and cedrusResponse.wasPressed:
                    clock.reset()
                    return (time, clock)

    def waitForKeys(self, nkeys=1, maxtime=1000, mask=None, clock=None, mintime=None, pressed=None, clearcue=None, fulltime=None, callout=None):
        # --- Set variables
        presses = 0
        events  = []

        # time correction if a custom clock is provided
        # reactionTime = HW reaction time + time correction
        timeCorrection = 0
        if clock is None:
            clock = core.MonotonicClock()
        # use base clock
        elif clock is 'base':
            clock = self.baseClock
            timeCorrection = clock.getTime()
        # custom clock
        else:
            timeCorrection = clock.getTime()

        # if we are using light sensor the sensor resets the timer
        if not self.lightSensor:
            self.dev.ResetRtTimer()
        else:
            timeCorrection = 0

        if pressed is None:
            pressed = [True]

        # --- Wait if minimum delay is given
        if mintime is not None:
            core.wait(mintime)

        # --- Clear cue
        if clearcue is None or clearcue is True:
            self.emptyCue()

        # --- Run the loop
        while maxtime > clock.getTime():
            self.dev.PollForResponse()

            # check for response
            if (self.dev.HasQueuedResponses()):
                # get time stamps
                responseTimeHW = self.dev.QueryRtTimer() // 1000.0 + timeCorrection
                responseTimeSW = clock.getTime()
                baseTime = self.baseClock.getTime()

                # process all responses
                while self.dev.HasQueuedResponses():
                    cedrusResponse = self.dev.GetNextResponse()
                    
                    # port has to be 0, port 2 are responses from light sensor
                    if cedrusResponse.port is 0:
                        # --- process response
                        if mask is not None and cedrusResponse.key not in mask:
                            continue

                        if cedrusResponse.wasPressed not in pressed:
                            continue

                        # --- callout
                        if callout is not None:
                            callout(cedrusResponse.key)

                        # --- convert pyxid2 response to old one
                        response = {'port': cedrusResponse.port,
                            'pressed': cedrusResponse.wasPressed,
                            'key': cedrusResponse.key,
                            'time': responseTimeHW,
                            'rtimeSW': responseTimeSW,
                            'rtimeHW': responseTimeHW,
                            'baseTime': baseTime,
                            'interface': 'Cedrus pyxid2'}

                        events.append(response)
                        presses += 1

                        if presses >= nkeys:
                            return events

        if fulltime is not None and clock.getTime() < fulltime:
            core.wait(fulltime - clock.getTime())

        return events

    def emptyCue(self):
        self.dev.ClearResponseQueue()

    def resetRTTimer(self):
        self.dev.ResetRtTimer()

    def setLightSensorThreshold(self, threshold):
        self.dev.SetAnalogInputThreshold(ord('A'), threshold)
#
# --- Cedrus pyxid: A version of Cedrus code that uses the old pyxid lib
#

class CedrusXID(object):
    """A class for wrapping cedrus related methods for the old pyxid library."""

    def __init__(self, sync=4, TR=None, dev=None):
        if (dev is None):
            import pyxid    

        for n in range(0, 3):
            try:
                if (dev is None):
                    self.dev = pyxid.get_xid_devices()[0]
                else:
                    self.dev = dev

                self.dev.reset_base_timer()
                # not used because of drift
                #self.dev.reset_rt_timer()
                #self.dev.con.send_xid_command("c13")
                self.syncKey = sync
                self.baseClock = core.MonotonicClock()
                break
            except:
                if n == 2:
                    print("\nERROR: Could not set up Cedrus response pad!\n")
                    raise

        self.TR = TR
        if TR is None:
            self.syncClock = False
        else:
            self.syncClock = core.Clock()


    def waitSync(self, sync=None, clock=None):

        if clock is None:
            clock = core.Clock()

        # --- are we simulating sync?
        if self.TR:
            while int(self.syncClock.getTime() * 100) % int(self.TR * 100):
                pass
            clock.reset()
            return (clock.getTime(), clock)

        # --- empty cue and wait for sync
        print("  --- waiting for sync pulse ---  ")
        self.emptyCue()

        if sync is None:
            sync = self.syncKey
        
        while True:
            self.dev.poll_for_response()
            while self.dev.response_queue_size():
                time = clock.getTime()
                response = self.dev.get_next_response()

                # --- process response
                if response['key'] == sync and response['pressed'] is True:
                    clock.reset()
                    return (time, clock)


    def waitForKeys(self, nkeys=1, maxtime=1000, mask=None, clock=None, mintime=None, pressed=None, clearcue=None, fulltime=None, callout=None):
        # --- Set variables
        presses = 0
        events  = []

        if clock is None:
            clock = core.MonotonicClock()
        elif clock is 'base':
            clock = self.baseClock

        if pressed is None:
            pressed = [True]

        # --- Wait if minimum delay is given
        if mintime is not None:
            core.wait(mintime)

        # --- Clear cue
        if clearcue is None or clearcue is True:
            self.emptyCue()

        # --- Run the loop
        while True and maxtime > clock.getTime():
            self.dev.poll_for_response()

            # check for response
            if (self.dev.HasQueuedResponses()):
                # get time stamps
                time = clock.getTime()
                baseTime = self.baseClock.getTime()

                # process all responses
                while self.dev.response_queue_size():

                    response = self.dev.get_next_response()

                    # --- process response
                    if mask is not None and response['key'] not in mask:
                        continue

                    if response['pressed'] not in pressed:
                        continue

                    # --- callout
                    if callout is not None:
                        callout(response['key'])

                    response['time'] = time
                    response['rtimeSW'] = time
                    response['rtimeHW'] = None
                    response['baseTime'] = baseTime
                    response['interface'] = 'Cedrus pyxid'

                    events.append(response)
                    presses += 1

                    if presses >= nkeys:
                        return events

        if fulltime is not None and clock.getTime() < fulltime:
            core.wait(fulltime - clock.getTime())

        return events

    def emptyCue(self):
        self.dev.poll_for_response()
        while self.dev.response_queue_size():
            self.dev.get_next_response()
            self.dev.poll_for_response()


#
# --- Cedrus ASCII: A version of Cedrus code that uses ASCII protocol
#

class CedrusASCII(object):
    """A class for wrapping cedrus related methods."""

    def __init__(self, sync=4, TR=None, dev=None):
        if (dev is None):
            import pyxid    

        for n in range(0, 3):
            try:
                if (dev is None):
                    self.dev = pyxid.get_xid_devices()[0]
                else:
                    self.dev = dev

                self.dev.reset_base_timer()
                # not used because of drift
                #self.dev.reset_rt_timer()
                #self.dev.con.send_xid_command("c13")
                self.syncKey = sync
                self.baseClock = core.MonotonicClock()
                break
            except:
                if n == 2:
                    print("\nERROR: Could not set up Cedrus response pad!\n")
                    raise
        self.TR = TR
        if TR is None:
            self.syncClock = False
        else:
            self.syncClock = core.Clock()


    def waitSync(self, sync=None, clock=None):

        if clock is None:
            clock = core.Clock()

        # --- are we simulating sync?

        if self.TR:
            while int(self.syncClock.getTime() * 100) % int(self.TR * 100):
                pass
            clock.reset()
            return (clock.getTime(), clock)

        # --- empty cue and wait for sync

        self.emptyCue()

        if sync is None:
            sync = self.syncKey

        while True:
            r = self.dev.con.read(1)
            if r:
                time = clock.getTime()
                try:
                    r = int(r)
                except:
                    pass

                # --- process response

                if r == sync:
                    clock.reset()
                    return (time, clock)


    def waitForKeys(self, nkeys=1, maxtime=1000, mask=None, clock=None, mintime=None, pressed=None, clearcue=None, fulltime=None, callout=None):

        # --- Set variables

        presses = 0
        events  = []

        if clock is None:
            clock = core.MonotonicClock()
            self.dev.reset_rt_timer() 
        elif clock is 'base':
            clock = self.baseClock

        if pressed is None:
            pressed = [True]

        # --- Wait if minimum delay is given

        if mintime is not None:
            core.wait(mintime)

        # --- Clear cue

        if clearcue is None or clearcue is True:
            self.emptyCue()

        # --- Run the loop

        while maxtime > clock.getTime() and presses < nkeys:
            r = self.dev.con.read(1)

            # process first response
            if r:
                # take time stamps
                time = clock.getTime()
                baseTime = self.baseClock.getTime()

                try:
                    r = int(r)
                except:
                    pass

                # --- process response

                if mask is not None and r not in mask:
                    continue

                if callout is not None:
                    callout(r)

                response = {'key': r,
                    'time': time,
                    'rtimeSW': time,
                    'rtimeHW': None,
                    'baseTime': baseTime,
                    'interface': 'Cedrus ASCII'}

                events.append(response)
                presses += 1

                if presses >= nkeys:
                    break

        if fulltime is not None and clock.getTime() < fulltime:
            core.wait(fulltime - clock.getTime())

        return events

    def emptyCue(self):

        while self.dev.con.read(1):
            pass


#
# --- Keyboard alternative to cedrus
#

class KeyboardASCII(object):
    """A class for wrapping cedrus related methods."""

    def __init__(self, sync=4, TR=None):
        self.syncKey = sync
        self.baseClock = core.MonotonicClock()

        self.TR = TR
        if TR is None:
            self.syncClock = False
        else:
            self.syncClock = core.Clock()


    def waitSync(self, sync=None, clock=None):

        if clock is None:
            clock = core.Clock()

        # --- are we simulating sync?

        if self.TR:
            core.wait(0.01)
            while int(self.syncClock.getTime() * 100) % int(self.TR * 100):
                pass
            clock.reset()
            return (clock.getTime(), clock)

        # --- empty cue and wait for sync

        self.emptyCue()

        if sync is None:
            sync = self.syncKey

        while True:
            r = self.dev.con.read(1)
            if r:
                time = clock.getTime()
                try:
                    r = int(r)
                except:
                    pass

                # --- process response

                if r == sync:
                    clock.reset()
                    return (time, clock)


    def waitForKeys(self, nkeys=1, maxtime=1000, mask=None, clock=None, mintime=None, fulltime=None, clearcue=None, callout=None):

            # --- Set variables

            presses = 0
            events  = []

            if clock is None:
                clock = core.MonotonicClock()
            elif clock is 'base':
                clock = self.baseClock
                
            if mask is not None:
                mask = [str(e) for e in mask]

            # --- Wait if minimum delay is given

            if mintime is not None:
                core.wait(mintime)

            if clearcue is None or clearcue is True:
                event.clearEvents()

            # --- Run the loop

            while maxtime > clock.getTime() and presses < nkeys:
                # allKeys = event.waitKeys(maxWait=maxtime - clock.getTime(), keyList=mask, timeStamped=clock, clearEvents=clearcue)
                allKeys = event.getKeys(keyList=mask, timeStamped=clock)

                baseTime = self.baseClock.getTime()

                if allKeys is not None:
                    for thisKey, thisTime in allKeys:
                        presses += 1
                        if callout is not None:
                            callout(thisKey)

                        response = {'key': thisKey,
                            'time': thisTime,
                            'rtimeSW': thisTime,
                            'rtimeHW': None,
                            'baseTime': baseTime,
                            'interface': 'Cedrus ASCII'}

                        events.append(response)

                        if presses >= nkeys:
                            break

                # event.clearEvents()

            if fulltime is not None and clock.getTime() < fulltime:
                core.wait(fulltime - clock.getTime())

            return events


    def emptyCue(self):

        event.clearEvents()


#
# --- Parallel codes
#


class gPar(object):
    """Class for light embedding of Parallel port interface using inpout32. Works in WinXP and WinVista"""

    def __init__(self, pport=0xec00, codelist=(), pduration=0.05, verbose=False):
        try:
            self.pp = windll.inpout32
            self.status = 'ok'
        except:
            self.pp = None
            self.status = 'fail'
            print("===> Warning, the parallel port is not functional!")
        self.pport = pport
        self.codelist = codelist
        self.codes = dict(codelist)
        self.pduration = pduration
        self.verbose = verbose

    def setValue(self, value):
        if self.pp is not None:
            self.pp.Out32(self.pport, value)
        if self.verbose:
            print("---> Par (%s) setValue: %d" % (self.status, value))

    def setCode(self, code):
        if self.pp is not None:
            self.pp.Out32(self.pport, self.codes[code])
        if self.verbose:
            print("---> Par (%s) setCode: %s (%d)" % (self.status, code, self.codes[code]))

    def sendValue(self, value, duration=None):
        if duration is None:
            duration = self.pduration
        if self.pp is not None:
            self.pp.Out32(self.pport, value)
            core.wait(duration)
            self.pp.Out32(self.pport, 0)
        if self.verbose:
            print("---> Par (%s) sendValue: %d, duration: %f" % (self.status, value, duration))

    def sendCode(self, code, duration=None):
        if duration is None:
            duration = self.pduration
        if self.pp is not None:
            self.pp.Out32(self.pport, self.codes[code])
            core.wait(duration)
            self.pp.Out32(self.pport, 0)
        if self.verbose:
            print("---> Par (%s) sendCode: %s (%d), duration: %f" % (self.status, code, self.codes[code], duration))

    def calibrateMarkers(self):
        print("---> EEG marker calibration")

        # --- onset

        core.wait(0.100)

        if self.pp is not None:

            for n in range(5):
                self.setValue(100)
                core.wait(0.030)
                self.setValue(0)
                core.wait(0.030)
        else:
            print("===> Warning, the parallel port is not functional!")

        # --- list codes

        core.wait(0.100)

        c = 0
        for (k, v) in self.codelist:
            c += 1
            print("     ... %03d: %s - %d" % (c, k, v))

            if self.pp is not None:
                for n in range(3):
                    self.setValue(v)
                    core.wait(0.050)
                    self.setValue(0)
                    core.wait(0.050)

        # --- offset

        core.wait(0.100)

        if self.pp is not None:
            for n in range(5):
                self.setValue(100)
                core.wait(0.030)
                self.setValue(0)
                core.wait(0.030)

        print("---> Done")



class gParNK(object):
    """Class for light embedding of Parallel port interface using dlportio (works in test mode on Win7."""

    def __init__(self, pport=0xd010, codelist=(), pduration=0.05, verbose=False):
        try:
            self.pp = windll.dlportio
            self.status = 'ok'
        except:
            self.pp = None
            self.status = 'fail'
            print("===> Warning, the parallel port is not functional!")
        self.pport = pport
        self.codelist = codelist
        self.codes = dict(codelist)
        self.pduration = pduration
        self.verbose = verbose

    def setValue(self, value):
        if self.pp is not None:
            self.pp.DlPortWritePortUchar(self.pport, 0)
            self.pp.DlPortWritePortUchar(self.pport, value)
        if self.verbose:
            print("---> Par (%s) setValue: %d" % (self.status, value))

    def setCode(self, code):
        if self.pp is not None:
            self.pp.DlPortWritePortUchar(self.pport, 0)
            self.pp.DlPortWritePortUchar(self.pport, self.codes[code])
        if self.verbose:
            print("---> Par (%s) setCode: %s (%d)" % (self.status, code, self.codes[code]))

    def sendValue(self, value, duration=None):
        if duration is None:
            duration = self.pduration
        if self.pp is not None:
            self.pp.DlPortWritePortUchar(self.pport, 0)
            self.pp.DlPortWritePortUchar(self.pport, value)
            core.wait(duration)
            self.pp.DlPortWritePortUchar(self.pport, 0)
        if self.verbose:
            print("---> Par (%s) sendValue: %d, duration: %f" % (self.status, value, duration))

    def sendCode(self, code, duration=None):
        if duration is None:
            duration = self.pduration
        if self.pp is not None:
            self.pp.DlPortWritePortUchar(self.pport, 0)
            self.pp.DlPortWritePortUchar(self.pport, self.codes[code])
            core.wait(duration)
            self.pp.DlPortWritePortUchar(self.pport, 0)
        if self.verbose:
            print("---> Par (%s) sendCode: %s (%d), duration: %f" % (self.status, code, self.codes[code], duration))

    def calibrateMarkers(self):
        print("---> EEG marker calibration")

        # --- onset

        core.wait(0.100)

        if self.pp is not None:

            for n in range(5):
                self.setValue(100)
                core.wait(0.030)
                self.setValue(0)
                core.wait(0.030)
        else:
            print("===> Warning, the parallel port is not functional!")

        # --- list codes

        core.wait(0.100)

        c = 0
        for (k, v) in self.codelist:
            c += 1
            print("     ... %03d: %s - %d" % (c, k, v))

            if self.pp is not None:
                for n in range(3):
                    self.setValue(v)
                    core.wait(0.050)
                    self.setValue(0)
                    core.wait(0.050)

        # --- offset

        core.wait(0.100)

        if self.pp is not None:
            for n in range(5):
                self.setValue(100)
                core.wait(0.030)
                self.setValue(0)
                core.wait(0.030)

        print("---> Done")



def latinSquare(n, i=0):
    nlist = collections.deque(range(n))
#    nlist.rotate(-i)
    nlist.rotate(1)
    lsq = list()
    for l in range(n):
        nlist.rotate(-1)
        elist = copy.deepcopy(nlist)
        eline = list()
        for e in range(n):
            if (e < 2 or e % 2 == 1):
                eline.append(elist.popleft())
            else:
                eline.append(elist.pop())
        lsq.append(eline)
    if n % 2 == 1:
        for l in range(n):
            nlist.rotate(-1)
            elist = copy.deepcopy(nlist)
            eline = list()
            for e in range(n):
                if (e < 2 or e % 2 == 1):
                    eline.append(elist.pop())
                else:
                    eline.append(elist.popleft())
            lsq.append(eline)
    lsq = collections.deque(lsq)
    lsq.rotate(-i)
    return(list(lsq))


def getItemsFrom(l, shuffle=True, last=None):
    m = []
    p = []
    while True:
        if len(m) == 0:
            if shuffle:
                random.shuffle(l)
                m = list(l)
                if last is not None and len(p) > last:
                    while (m[0] in p[-last:]) or (p[-1] in m[:last]):
                        random.shuffle(l)
                        m = list(l)
            else:
                m = list(l)
        i = m.pop(0)
        p.append(i)
        yield i


def getTextInput(win, text, elements=None, clock=None):

    if clock is None:
        clock = core.Clock()

    chars = u'abcčdefghijklmnopqrsštuvwxyzžABCČDEFGHIJKLMNOPQRSŠTUVWXYZŽ ,!?'
    maps = {'semicolon': u'č', 'bracketleft': u'š', 'backslash': u'ž', 'space': u' ', 'comma': u',', 'period': u'.', 'minus': u'-'}

    text.setText('')

    while True:

        text.draw()
        if elements is not None:
            for e in elements:
                e.draw()
        win.flip()

        response = event.waitKeys()
        if response:
            if response[0] == 'backspace' and len(text.text) > 0:
                text.setText(text.text[:-1])

            elif response[0] == 'return':
                break

            elif response[0] in maps:
                text.setText(text.text + maps[response[0]])

            elif response[0] in chars:
                text.setText(text.text + response[0])

    return (text.text, clock.getTime())


#
# --- Send data to server
#

def sendResults(url=None, subject=None, session=None, code=None, name=None, data=None, filename=None, raw=False):

    # --- Check we have all to send the data

    if not requests:
        print("ERROR: Requests library not present. Could not send results!")
        return

    if url is None:
        print("ERROR: No address provided! Could not send results!")
        return

    if data is None and filename is None:
        print("ERROR: No data or file provided! Could not send results!")
        return

    if filename is not None and not os.path.exists(filename):
        print("ERROR: The provided file does not exist! Could not send results!")
        return
    else:
        if data is None:
            data = open(filename, 'rb').read()
        else:
            data += open(filename, 'rb').read()

    # --- Sort subject session and the rest

    if subject is None:
        subject = "subj-" + data.getDateStr(format='%Y.%m.%d.%H%M%S')
    if session is None:
        session = "sess-" + data.getDateStr(format='%Y.%m.%d.%H%M%S')
    if code is None:
        code = "Unknown"
    if name is None:
        name = "Unknown"

    # --- Send the stuff

    if raw:
        action = "savefile"
    else:
        action = "saveresults"

    post = {'subject': subject, 'session': session, 'code': code, 'name': name, 'action': action, 'data': data}
    r = requests.post(url, data=post)
    if 'ok' in r.text:
        print("Data saved successfully to server! Local copy also saved.")
    else:
        print("WARNING: Data not saved to server! Use local copy.")


# -------------------------------------------------------------------------------
# Name:        get_image_size
# Purpose:     extract image dimensions given a file path using just
#              core modules
#
# Author:      Paulo Scardine (based on code from Emmanuel VAÏSSE)
#
# Created:     26/09/2013
# Copyright:   (c) Paulo Scardine 2013
# Licence:     MIT
# -------------------------------------------------------------------------------


class UnknownImageFormat(Exception):
    pass


def getImageSize(file_path):
    """
    Return (width, height) for a given img file content - no external
    dependencies except the os and struct modules from core
    """
    size = os.path.getsize(file_path)

    with open(file_path) as input:
        height = -1
        width = -1
        data = input.read(25)

        if (size >= 10) and data[:6] in ('GIF87a', 'GIF89a'):
            # GIFs
            w, h = struct.unpack("<HH", data[6:10])
            width = int(w)
            height = int(h)
        elif ((size >= 24) and data.startswith('\211PNG\r\n\032\n')
              and (data[12:16] == 'IHDR')):
            # PNGs
            w, h = struct.unpack(">LL", data[16:24])
            width = int(w)
            height = int(h)
        elif (size >= 16) and data.startswith('\211PNG\r\n\032\n'):
            # older PNGs?
            w, h = struct.unpack(">LL", data[8:16])
            width = int(w)
            height = int(h)
        elif (size >= 2) and data.startswith('\377\330'):
            # JPEG
            msg = " raised while trying to decode as JPEG."
            input.seek(0)
            input.read(2)
            b = input.read(1)
            try:
                while (b and ord(b) != 0xDA):
                    while (ord(b) != 0xFF):
                        b = input.read(1)
                    while (ord(b) == 0xFF):
                        b = input.read(1)
                    if (ord(b) >= 0xC0 and ord(b) <= 0xC3):
                        input.read(3)
                        h, w = struct.unpack(">HH", input.read(4))
                        break
                    else:
                        input.read(int(struct.unpack(">H", input.read(2))[0]) - 2)
                    b = input.read(1)
                width = int(w)
                height = int(h)
            except struct.error:
                raise UnknownImageFormat("StructError" + msg)
            except ValueError:
                raise UnknownImageFormat("ValueError" + msg)
            except Exception as e:
                raise UnknownImageFormat(e.__class__.__name__ + msg)
        else:
            raise UnknownImageFormat(
                "Sorry, don't know how to get information from this file."
            )

    return width, height


# ---> core functions
# random item from a list generator _ added by AV from gpsy3
def get_items_from(l, shuffle=True, last=None):
    """
    A function that creates a generator for returning random items from lists.
    
    Parameters:
    l -- a list
    shuffle -- shuffle order of items in the list (default = True)
    last -- prevent repetition of last x elements (default = None)
    """
    m = []
    p = []
    while True:
        if len(m) == 0:
            if shuffle:
                random.shuffle(l)
                m = list(l)
                if last is not None and len(p) > last:
                    while (m[0] in p[-last:]) or (p[-1] in m[:last]):
                        random.shuffle(l)
                        m = list(l)
            else:
                m = list(l)
        i = m.pop(0)
        p.append(i)
        yield i

