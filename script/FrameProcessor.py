import threading as mt
import numpy as np
import time
import cv2
from TimeStamp import TimeStamp

class FrameProcessor(mt.Thread):
    def __init__(self, name, owner, terminate, frameQ, msgQ, resultFrameQ):
        super(FrameProcessor, self).__init__()
        self.name = name
        self.event = mt.Event()
        self.owner = owner
        self.terminate = terminate
        self.msgQ = msgQ
        self.frameQ = frameQ
        self.resultFrameQ = resultFrameQ
        self.ts = TimeStamp("FrameProcessor")
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.time_collector = []
        self.start()
        
    def run(self):
        while not self.terminate.is_set():
            if self.event.wait(1):
                try:
                    time_frame_tuple = self.frameQ.get_nowait()
                    self.process(time_frame_tuple)
                except:
                    # print(f"[{self.ts.time()}][{self.name}] trouble when runnig")
                    pass
                finally:
                    self.event.clear()  # Reset the stream and event
                    with self.owner.lock: # Return itself to the available pool
                        self.owner.pool.append(self)

    def process(self, time_frame_tuple):
        '''
        The frame processing function
        '''

        ## uncomment this to store time record
        # self.time_collector.append((incoming_time, 1000*self.ts.time("second")+self.ts.time("msec")))
        
        incoming_time, frame = time_frame_tuple
        org_frame = frame.copy() # copy an original frame for further usage
        
        #### 
        # Implement your frmae process here...
        process_message = None 
        ###
        
        try:
            self.msgQ.put_nowait((incoming_time, process_message))
            self.resultFrameQ.put_nowait((incoming_time, org_frame))
        except:
            pass
        
