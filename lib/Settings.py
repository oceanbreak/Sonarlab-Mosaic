"""
Module to read and write to settings file
"""

SETTINGS_FILE = 'settings.cfg'

class Settings:

    def __init__(self):
        self.keys = ['directory', 'mapscale', 'cableout']
        self.directory = ''
        self.map_scale = 1.0
        self.cable_out = None
        self.readfile()


    def __str__(self):
        return f'{self.keys[0]}:{self.directory}\n' + \
                f'{self.keys[1]}:{self.map_scale:.1f}\n' + \
                f'{self.keys[2]}:{self.cable_out}\n'


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