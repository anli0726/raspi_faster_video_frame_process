import picamera
from picamera.array import PiRGBAnalysis
import time
import queue
from FrameProcessor import FrameProcessor
import threading as mt
from TimeStamp import TimeStamp
import cv2
import numpy as np


class VideoCapture(PiRGBAnalysis):
    '''
    A costum, file-like output. It is a subclass of PiRGBAnalysis.
    The analyse function will provide an np.array for image processing
    '''

    def __init__(self, camera):
        super(VideoCapture, self).__init__(camera)
        self.frameQ = queue.Queue() # queue to store incoming video frame
        self.msgQ = queue.PriorityQueue() # priority queue to store processing result
        self.resultFrameQ = queue.PriorityQueue() # priority queue to store processed frame
        self.terminate = mt.Event() # a threading event (flag) to notify all threads the end of the process

        self.t_pring_msg = mt.Thread(target=self.print_msg).start() # thread to show processing result concurrently
        self.t_visual = mt.Thread(target=self.show).start() # thread to show processed frame concurrently

        self.ts = TimeStamp("VideoCapture TS") # time-stamp object
        self.cap_frame_count = 0
        self.cap_start = None

        # lists to store the excecuting time (in msec) of different funcitons
        self.time_collector_frameCap = []
        self.time_collector_print = []
        self.time_collector_show = []

    def analyse(self, frame):
        frame_time = 1000*self.ts.time("second")+self.ts.time("msec")

        ## uncomment this to shoe frame capture fps
        # if self.cap_frame_count == 0:
        #     self.cap_start = time.time()
        # self.cap_frame_count += 1

        time_frame_tuple = (frame_time, frame)
        self.process(time_frame_tuple)

        ## uncomment this to shoe frame capture fps
        # if time.time() - self.cap_start >= 1:
        #     print(f"[{self.ts.time()}][analyse] capture fps: {self.cap_frame_count}")
        #     self.cap_frame_count = 0
        


    def print_msg(self):
        while not self.terminate.is_set():
            try:
                _, msg = self.msgQ.get()
                print(f"[{self.ts.time()}][print_msg] {msg}")
            except:
                pass

    def show(self):
        # cv2.namedWindow("result", cv2.WINDOW_NORMAL)
        # cv2.resizeWindow("result", self.frame_shape[0]//2, self.frame_shape[1]//2)

        while not self.terminate.is_set():
            try:
                _, result_frame = self.resultFrameQ.get_nowait()
                cv2.imshow("result", result_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.terminate.set()
            except:
                pass
    
    def process(self, time_frame_tuple):
       '''
        The frame processing function
        '''
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
        


if __name__ == "__main__":
  
    with picamera.PiCamera() as camera:
        camera.resolution = (1640, 1232) # set camera resolution
        camera.framerate = 40 # set camera framerate
        cap = VideoCapture(camera) 

        camera.start_recording(cap, 'bgr') # recording video into 'bgr' (opencv) format

        while not VideoCapture.terminate.is_set():
            camera.wait_recording()
        camera.stop_recording()

        ## for recording specific time 
        # while time.time() - start_time < 3:
        #     camera.wait_recording()
        # camera.stop_recording()
        # cap.terminate.set()
