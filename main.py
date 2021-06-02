from __future__ import print_function, division
from posixpath import basename
from psychopy import core, data, event, gui, visual, sound
import os.path
import sys
import time
#from rdoclient_py3 import RandomOrgClient

sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))
import base
from stimulator import UART

class visual_stim():
    def __init__(self):

        self.random_number = None  
        self.experiment_info = None         

        
        #moras naredit še log
        self.user_input_text()
        self.text_screen()
        self.screen_settings()
        self.visual_objects()
        self.experiment_choice()
        self.logger_start()

        self.title.draw()
        self.instructions.draw()
        self.win.flip()
        event.waitKeys(keyList="space")
        self.win.flip()
        self.fixation.draw()
        self.win.flip()


    def text_screen(self):
        self.text = {
        "Slovene": {
            "title": u"Naloga stimuliranje vagus živca",
            "instructions": u"V tej nalogi se bo v blokih izvajala stimulacija vagusa...",
            "report": u"Snemanje je zaključeno.",},
        "English": {
            "title": u"...",
            "instructions": u"This task ....",
            "report": u"Recording completed.",}
            }

 
    def user_input_text(self):
        self.experiment_info = { "Language": ["Slovene", "English"],
                            "Subject": "0_test",
                            "Practice run": False,
                            "Tok stimulusa [microA]": 200,
                            "block sequence": 1,
                            "MRI TR": 1.3}

        dialog = gui.DlgFromDict(self.experiment_info, title=u"tVNS")
        if not dialog.OK:
            core.quit()
    
    def screen_settings(self):
        self.screen      = 2                 # which screen to use
        self.flip        = False             # flip screen AV
        self.color_space = "rgb255"          # rgb color space
        self.background  = [0, 0, 0]         # background color
        self.win_width   = 1920              # window width
        self.win_height  = 1080              # window height
        self.wrap_width  = self.win_width * 0.6   # safety zone for text

        self.fixation_radius     = 10                # fixation point size
        self.fixation_linewidth  = 5                 # width of line around fixation point
        self.fixation_color      = [78, 78, 78]      # color

        self.title_color         = [160, 160, 160]   # title color
        self.title_height        = 50                # title size
        self.instructions_color  = [190, 190, 190]   # text color
        self.instructions_height = 30                # text size
        self.report_color        = [150, 150, 150]   # report text color
        self.report_height       = 30                # report text size


    def visual_objects(self):

        self.win = visual.Window([self.win_width, self.win_height],
                    winType="pygame",
                    screen=self.screen,
                    fullscr=False,
                    allowGUI=False,
                    waitBlanking=True,
                    color=self.background,
                    colorSpace=self.color_space,
                    units="pix",
                    pos=[0,0])



        self.title = visual.TextStim(win=self.win, text=self.text[self.experiment_info["Language"]]["title"], pos=[0, 0.2 * self.win_height], color=self.title_color, colorSpace=self.color_space, height=self.title_height, wrapWidth=self.wrap_width, bold=True, flipHoriz=self.flip)

        self.instructions = visual.TextStim(win=self.win, text=self.text[self.experiment_info["Language"]]["instructions"], pos=[0, -0.1 * self.win_height], color=self.instructions_color, colorSpace=self.color_space, height=self.instructions_height, wrapWidth=self.wrap_width, flipHoriz=self.flip)

        self.report = visual.TextStim(win=self.win, text=self.text[self.experiment_info["Language"]]["report"], pos=[0, 0], color=self.report_color, colorSpace=self.color_space, height=self.report_height, wrapWidth=self.wrap_width, flipHoriz=self.flip)

        self.fixation = visual.Circle(win=self.win, pos=[0, 0], radius=self.fixation_radius, lineColor=self.fixation_color, fillColor=self.fixation_color, lineColorSpace=self.color_space, fillColorSpace=self.color_space, lineWidth=self.fixation_linewidth, units="pix")


    def logger_start(self):
        log_folder = os.path.join("..", "results", "tVNS")
        if not os.path.exists(log_folder):
            print("===> Creating folder %s to store results!" % (log_folder))
            os.makedirs(log_folder)
        self.log_file = open(os.path.join(log_folder, "tVNS-%s-%s.txt" % (self.experiment_info["Subject"], data.getDateStr(format="%Y.%m.%d.%H%M%S"))), "w")
        print("# Starting log file for subject %s at %s" % (self.experiment_info["Subject"], data.getDateStr(format="%d.%m.%Y, %H:%M:%S")), file=self.log_file)


    def experiment_choice(self):
        syncButton = 5  
        if self.experiment_info["Practice run"] == False:
            self.n_trials = 100
            self.flip = True
            self.cedruss = base.CedrusASCII(syncButton)
            self.external_triger = 1  
            self.posX = 1280  
        else:
            self.n_trials = 20000
            self.TR = float(self.experiment_info["MRI TR"]) 
            self.cedruss = base.KeyboardASCII(syncButton, self.TR)
            self.external_triger = 0
            self.flip = False
            self.posX = 0  
            self.betweenStim_numberOFstim = 1
        
    def returner(self):
        return (self.cedruss, self.n_trials)

    def script_ender(self):
        # wait
        core.wait(2)

        # cleanup
        print("===> Recording stopped - %s" %  ((data.getDateStr(format="%Y-%m-%d %H:%M:%S"))))
        print("# Recording stopped %s" % ((data.getDateStr(format="%Y-%m-%d %H:%M:%S"))), file=self.log_file)

        # ---> show end message
        self.report.draw()
        self.win.flip()
        print("# End message shown %s" % ((data.getDateStr(format="%Y-%m-%d %H:%M:%S"))), file=self.log_file)
        print("===> Showing report, press any key to end script!")
        # AV interface.wait_for_keys()
        self.cedruss.waitForKeys()

        # ---> end script
        print("# Ending script %s" % ((data.getDateStr(format="%Y-%m-%d %H:%M:%S"))), file=self.log_file)
        self.log_file.close()
        self.win.close()
        core.quit()

            
class exp_block():
    def __init__(self, port = "COM3", baudrate = 9600):
        self.port = port
        self.baudrate = baudrate

        self.uart = UART(self.port, self.baudrate, 0.5)


    def stim(self, period = 10000, pulse_width = 300, biphase = 2, current = 300, duration_minutes = 0, duration_seconds = 20, after_seconds = 10, number_of_wagons = 6, 
            stim_ONOFF_mode2 = 1, between_pulse_period = 80, mode = 0, send_new_command = True):
        self.uart.open_port()
        if send_new_command == True:
            self.uart.send(f"PARAMS-pr{period}-ln{pulse_width}-bp{biphase}-cr{current}-md{mode}-sp{stim_ONOFF_mode2}-dh0-dm{duration_minutes}-ds{duration_seconds}-ah0-am0-as{after_seconds}-tm{number_of_wagons}-sh0-sm0-ss1-st1-wp{between_pulse_period}-es0!")
        time.sleep(1)
        self.uart.send("status!")
        self.uart.receive(350)
        self.uart.close_port()

    def randomizator_blokov(self):
        r = RandomOrgClient("47f62947-d7ca-45c0-96bf-1c6fe74c12c1")
        self.random_number = r.generate_integers(1, 1, 3)



if __name__ == "__main__":
    stimulacija = exp_block()
    eksperiment1 = visual_stim()
    
    cedruss, n_trials = eksperiment1.returner()
    stimulacija.stim(mode = 2, send_new_command = True)

    terminate = False
    for trial in range(n_trials):
        # quit the experiment with the q key
        if event.getKeys(keyList=['q', 'Q']):
#            print("===> Script ended preliminary via the q key (%s)" % ((data.getDateStr(format="%Y-%m-%d %H:%M:%S"))))
#            print("# Script ended preliminary via the q key (%s)" % ((data.getDateStr(format="%Y-%m-%d %H:%M:%S"))), file=log_file)
            terminate = True
            #################################
            stimulacija.stim(mode = 0) # tukaj mora ugasnit
            #################################
            core.quit()
            break

        # AV try to sync every stimuly with MR pulse (TR) when immaging of new volume starts
        TMtime, boldClock = cedruss.waitSync()
        if trial % 10 == 0:
            stimulacija.stim(send_new_command = False) # Mora dobit samo informacije

        print("==> we are in # %d loop" % trial)
        
        if terminate == True:
            break
    stimulacija.stim(mode = 0)
    eksperiment1.script_ender()
