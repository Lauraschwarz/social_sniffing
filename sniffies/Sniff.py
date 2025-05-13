import numpy as np
import pandas as pd

from handle_rawdata import create_reader

class Sniff(object):

   def __init__(directory, 
        mouseID,
        start,
        end, 
        frame_rate, 
        module=behav):
        """
        Initialize the Sniff object with the given parameters.  
        :param folder: The folder where the data is stored.
        :param data: Analog data stream from Harp behaviour box. harp-python reader required
        outputset: send command for activating lickports. DIOport0 and DIOport1 are the portlights (Set means turn on lights). 
                    SupplyPOrt0 and SupplyPort1 the valves/ rewarddelivery
        outputclear: send command to clear the command (switch off lights and/or valves). 
        digitalinputstate: digital input state of the lickports. (detection of when the mouse pokes its head in the port)
        """
        self.data = analogdata
        self.directory = directory
        self.module = module
        self.start = start
        self.end = end
        self.frame_rate = frame_rate

        analogdata = create_reader(directory, mouseID, module, register='44')
        outputset = create_reader(directory, mouseID, module, register='34')
        outputclear = create_reader(directory, mouseID, module, register='35')
        digitalinputstate = create_reader(directory, mouseID, module, register='32')

        self.analograw = analogdata.between_time(start, end)
        self.analograw = self.analograw['AnalogInput0']