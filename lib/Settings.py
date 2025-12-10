"""
Module to read and write to settings file
"""

SETTINGS_FILE = 'settings.cfg'

class Settings:

    def __init__(self):
        self.keys = ['directory', 'mapscale', 'cableout', 'margins',
                     'gamma', 'corwindow', 'slantthreshold', 'startsearchbottom', 'stripescale',
                     'debug']
        self.directory = ''
        self.map_scale = 1.0
        self.cable_out = None
        self.map_margins = 10 # Margins of map in meters
        self.gamma = 1.0
        self.corwindow = 11
        self.slantthreshold = 0
        self.startsearchbottom = 0
        self.stripescale = 1
        self.debug=False
        self.readfile()


    def __str__(self):
        return f'{self.keys[0]}:{self.directory}\n' + \
                f'{self.keys[1]}:{self.map_scale:.1f}\n' + \
                f'{self.keys[2]}:{self.cable_out:.0f}\n' + \
                f'{self.keys[3]}:{self.map_margins}\n' + \
                f'{self.keys[4]}:{self.gamma:.1f}\n' + \
                f'{self.keys[5]}:{self.corwindow}\n' + \
                f'{self.keys[6]}:{self.slantthreshold}\n' + \
                f'{self.keys[7]}:{self.startsearchbottom}\n' + \
                f'{self.keys[8]}:{self.stripescale}\n' + \
                f'{self.keys[9]}:{self.debug}\n'


    def readfile(self):
        with open(SETTINGS_FILE, 'r') as sett_read:
            for line in sett_read:
                # Path
                if self.keys[0] in line:
                    self.directory = line.split(':')[1].rstrip()
                # Map Scale
                if self.keys[1] in line:
                    self.map_scale = float(line.split(':')[1])
                # Cable Out
                if self.keys[2] in line:
                    cable_out = int(line.split(':')[1])
                    if cable_out < 0:
                        self.cable_out = None
                    else:
                        self.cable_out = cable_out
                # Margins
                if self.keys[3] in line:
                    self.map_margins = int(line.split(':')[1])
                # Gamma
                if self.keys[4] in line:
                    self.gamma = float(line.split(':')[1])
                # Correction window
                if self.keys[5] in line:
                    corwindow = int(line.split(':')[1])
                    self.corwindow = corwindow if corwindow%2 == 1 else corwindow + 1
                # Slant range threshold
                if self.keys[6] in line:
                    self.slantthreshold = int(line.split(':')[1])
                # Start search bottom
                if self.keys[7] in line:
                    self.startsearchbottom = int(line.split(':')[1])
                # Stripe scale
                if self.keys[8] in line:
                    self.stripescale = int(line.split(':')[1])
                                    # Stripe scale
                if self.keys[9] in line:
                    self.debug = int(line.split(':')[1])

    def writefile(self):
        if self.cable_out is None:
            cable_out = -1
        else:
            cable_out = self.cable_out
        with open(SETTINGS_FILE, 'w') as sett_write:
            # Directory
            sett_write.write(f'{self.keys[0]}:{self.directory}\n') 
            sett_write.write(f'{self.keys[1]}:{self.map_scale:.1f}\n') 
            sett_write.write(f'{self.keys[2]}:{cable_out:.0f}\n') 
            sett_write.write(f'{self.keys[3]}:{self.map_margins:.0f}\n') 
            sett_write.write(f'{self.keys[4]}:{self.gamma:.1f}\n') 
            sett_write.write(f'{self.keys[5]}:{self.corwindow:.0f}\n') 
            sett_write.write(f'{self.keys[6]}:{self.slantthreshold:.0f}\n')
            sett_write.write(f'{self.keys[7]}:{self.startsearchbottom:.0f}\n')
            sett_write.write(f'{self.keys[8]}:{self.stripescale:.0f}\n')
            sett_write.write(f'{self.keys[9]}:{self.debug:.0f}\n')