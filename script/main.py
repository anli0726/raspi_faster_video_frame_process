import picamera
from picamera.array import PiRGBAnalysis
from FrameProcessor import *
import queue

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
        self.frame_shape = (camera.resolution[0], camera.resolution[1])

        # frame processor pool
        self.pool = [FrameProcessor(f"FP{i+1}", 
                                    self,
                                    self.terminate,
                                    self.frameQ, 
                                    self.msgQ, 
                                    self.resultFrameQ) for i in range(4)] 
        self.processor = None
        self.lock = mt.Lock()
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

        ## uncomment this to store the incoming time (in msec) per video frame
        # self.time_collector_frameCap.append((frame_time, frame_time))

        ## uncomment this to shoe frame capture fps
        # if self.cap_frame_count == 0:
        #     self.cap_start = time.time()
        # self.cap_frame_count += 1

        # New frame; set the current processor is ungoing
        if self.processor:
            self.processor.event.set()

        with self.lock: # prevent dead lock situation
            '''
            grab a spare frame processor if available, 
            else set self.processor to None to indicate that all of them are working 
            '''
            if len(self.pool): 
                self.processor = self.pool.pop()
            else:
                self.processor = None

        if self.processor:
            try:
                # create a tuple of the incoming time of the frame and the frame itself
                # and put the tuple into the queue
                self.frameQ.put_nowait((frame_time, frame))
            except:
                pass
        
        # self.print_msg_single()
        # self.show_single()
        
        ## uncomment this to shoe frame capture fps
        # if time.time() - self.cap_start >= 1:
        #     print(f"[{self.ts.time()}][analyse] capture fps: {self.cap_frame_count}")
        #     self.cap_frame_count = 0
        

    def print_msg_single(self):
        '''
        print procseeing result one at a time; uncomment it in "analyse"
        if you want to print out one along with incoming frame
        '''
        try:
            p, msg = self.msgQ.get_nowait() # get the processing reuslt following its priority
            print(f"[{self.ts.time()}][print_msg] {msg}")
        except:
            pass
    
    
    def show_single(self):
        '''
        show procseed frame one at a time; uncomment it in "analyse"
        if you want to show one along with incoming frame
        '''
        try:
            p, result_frame = self.resultFrameQ.get_nowait() # get the processed frame following its priority
            cv2.imshow("result", result_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): # press q to terminate the recording process 
                self.terminate.set()
        except:
            pass



    def print_msg(self):
        '''
        threading version of print_msg_single function
        '''
        while not self.terminate.is_set():
            try:
                p, msg = self.msgQ.get()

                ## uncomment this to store when print_msg been called
                # self.time_collector_print.append((p, 1000*self.ts.time("second")+self.ts.time("msec")))

                print(f"[{self.ts.time()}][print_msg] p = {p}")
                print(f"[{self.ts.time()}][print_msg] {msg}")
            except:
                # print(f"[{self.ts.time()}][print_msg] Error happened")
                pass
    
    def show(self):
        '''
        threading version of show function
        '''
        # cv2.namedWindow("result", cv2.WINDOW_NORMAL)
        # cv2.resizeWindow("result", self.frame_shape[0], self.frame_shape[1]//2)

        while not self.terminate.is_set():
            try:
                p, result_frame = self.resultFrameQ.get()

                ## uncomment this to store when show been called
                # self.time_collector_show.append(1000*self.ts.time("second")+self.ts.time("msec"))
                
                print(f"[{self.ts.time()}][show] p = {p}")
                cv2.imshow("result", result_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.terminate.set()
            except:
                # print(f"[{self.ts.time()}][show] Error happened")
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

        # empty every queue
        while (not cap.frameQ.empty()) \
            or (not cap.resultFrameQ.empty()) \
            or (not cap.msgQ.empty()):
            
            if not cap.frameQ.empty():
                cap.frameQ.get()
                print(f"cap.frameQ.qsize() = {cap.frameQ.qsize()}")

            if not cap.resultFrameQ.empty():
                cap.resultFrameQ.get()
                print(f"cap.resultFrameQ.qsize() = {cap.resultFrameQ.qsize()}")

            if not cap.msgQ.empty():
                cap.msgQ.get()
                print(f"cap.msgQ.qsize() = {cap.msgQ.qsize()}")

        for fp in cap.pool:
            fp.join()

        

