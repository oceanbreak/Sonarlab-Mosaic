import os
import numpy as np

#### Структура данных файлов RASTR ######

class DataStructure:

    def __init__(self, file_path):
        fname_base = '.'.join(file_path.split('.')[:-1])
        self.lft = fname_base + '.lft'
        self.rgt = fname_base + '.rgt'
        self.n_v = fname_base + '.n_v'
        self.base_name = fname_base

class BaseRastrData:

    def __init__(self):

        self.items = {}
        
    def writeItem(self, item_name, value):
        if item_name not in self.items:
            print('ERROR: Invalid item')
            raise(TypeError)
        else:
            self.items[item_name] = value

    def getItem(self, item_name):
        if item_name not in self.items:
                print('Invalid item')
                raise(TypeError, 'Invalid Item')
        else:
            return self.items[item_name]
            
    def __str__(self):
        ret_str = ''
        for key in self.items.keys():
            ret_str += f'{key} : {self.items[key]}\n'
        return ret_str


class RastrFileHeader(BaseRastrData):

    def __init__(self):

        self.items ={"password" : None,
            "version" : None,
            "coding_mode" : None,
            "FILE_TITLE_size" : None,
            "BLOCK_TITLE_size" : None,
            "begin_time" : None,
            "device" : None,
            "report" : None}


class RastrBlockHeader(BaseRastrData):

    def __init__(self):
        self.items = {"device" : None,
                      "current_data_size" : None,
                      "previous_data_size" : None,
                      "sec" : None,
                      "min" : None,
                      "hour" : None,
                      "day" : None,
                      "month" : None,
                      "year" : None,
                      "delta_time" : None,
                      "string_size" : None,
                      "string_number" : None,
                      "frequency" : None}

class RastrNavLine(BaseRastrData):

    def __init__(self):
        self.items = {"lattitude" : None,
                "longtitude" : None,
                "sec" : None,
                "min" : None,
                "hour" : None,
                "day" : None,
                "month" : None,
                "year" : None}
