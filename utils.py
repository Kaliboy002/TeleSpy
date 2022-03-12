# https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
import os
import cv2
import wave
import pyaudio
import subprocess
from threading import Thread
from datetime import datetime
from time import perf_counter_ns, perf_counter, sleep,time
# import moviepy.editor as mpe


# https://stackoverflow.com/questions/14140495/how-to-capture-a-video-and-audio-in-python-from-a-camera-or-webcam

def timeStamp():
    return datetime.now().strftime('%d%m%Y_%H%M%S')


def takeScreenShot(fileName):
    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # 0 -> index of camera

    # The resolution of the camera
    # width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    # height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    # print(width, height)

    # set resolution of the photo taken
    # cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    # cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    s, img = cam.read()
    if s:  # frame captured without any errors
        cv2.imwrite(fileName, img)  #save image
    cv2.destroyAllWindows()
    return fileName




def getEnv(var, cast=None, isList=False):
    value = os.getenv(var)
    if isList:
        value = [ cast(i) if cast else i for i in value.split()]
    if cast and not isList:
        value = cast(value)
    return value



def removeFile(*fileList):
    for file in fileList:
        if(os.path.exists(file)): 
            os.remove(file)


class AudioRecorder:

    def __init__(self) -> None:
        self.running = False

        self.chunk = 1024  # Record in chunks of 1024 samples
        self.sample_format = pyaudio.paInt16  # 16 bits per sample
        self.channels = 1
        self.fs = 44100  # Record at 44100 samples per second

        self.p = pyaudio.PyAudio()  # Create an interface to PortAudio

        # Store data in chunks for 3 seconds
        # for i in range(0, int(self.fs / self.chunk * self.seconds)):
        # self.chunkInEachSec = int(self.fs / self.chunk)

        self.stream = self.p.open(format=self.sample_format,
                                  channels=self.channels,
                                  rate=self.fs,
                                  frames_per_buffer=self.chunk,
                                  input=True)

    def startAudio(self):

        self.frames = []  # Initialize array to store frames
        self.running = True
        self.stream.start_stream()
        # try:
        count = 0
        while self.running:
            count += 1
            # if self.stream.is_stopped():
            #     print('stopped')
            #     break
            data = self.stream.read(self.chunk)
            self.frames.append(data)
            # if count%self.chunkInEachSec==0: # print every second
            #     print(count,'recording')
        # except Exception as e:
        #     print("exception occured", e)

    def start(self):
        self.th = Thread(target=self.startAudio)
        self.th.start()

    def stop(self, file=None):
        if not self.running : return
        self.running = False
        # Stop and close the self.stream
        self.stream.stop_stream()
        self.stream.close()
        # Terminate the PortAudio interface
        self.p.terminate()
        if file: # if file not present then it won't be saved
            # print('Finished recording')
            # Save the recorded data as a WAV file
            wf = wave.open(file, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.p.get_sample_size(self.sample_format))
            wf.setframerate(self.fs)
            wf.writeframes(b''.join(self.frames))
            wf.close()
        self.th.join()


class VideoRecorder():

    # Video class based on openCV
    def __init__(self,fps=15):
        self.running = False
        self.device_index = 0
        self.fps = fps  # fps should be the minimum constant rate at which the camera can
        # self.fourcc = "MJPG"  # capture images (with no decrease in speed over time; testing is required)
        self.fourcc = "XVID"  # capture images (with no decrease in speed over time; testing is required)
        self.frames = self.getWidthHeight()
        self.tempFile = 'temp.avi'
        removeFile(self.tempFile)
        # print(self.getWidthHeight())

        self.video_writer = cv2.VideoWriter_fourcc(*self.fourcc)

        self.frame_counts = 1
        # check this


    # Video starts being recorded
    def record(self):
        self.running = True

        self.video_out = cv2.VideoWriter(self.tempFile, self.video_writer, self.fps, self.frames)
        self.video_cap = cv2.VideoCapture(self.device_index, cv2.CAP_DSHOW)
        # check with time instead of perf_counter

        self.starttime = time()
        self.framescount = 0

        while self.running:
            # opencv doesn't record video in a constant frames per second, so wait for the time to pass before capturing
            # to make a constant video renderer
            # if (perf_counter() - oldTime) * self.fps > 1:
            ret, video_frame = self.video_cap.read()
            if ret and self.video_out.isOpened():
                self.video_out.write(video_frame)
                self.framescount +=1
                # oldTime = perf_counter()
                # gray = cv2.cvtColor(video_frame, cv2.COLOR_BGR2GRAY)
                # cv2.imshow('video_frame', gray)
                # cv2.waitKey(1)


    def getWidthHeight(self):
        cap = cv2.VideoCapture(self.device_index, cv2.CAP_DSHOW)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        cv2.destroyAllWindows()
        return width, height

    def stop(self,file=None):
        # returns effective frames per seceon
        if not self.running: return

        totalTime = time() - self.starttime
        self.running = False
        self.video_out.release()
        self.video_cap.release()
        cv2.destroyAllWindows()
        self.th.join()
        if file:
            os.replace(self.tempFile, file)
            # subprocess.call(f"ffmpeg -r {self.framescount/totalTime} -i {self.tempFile} -r {self.fps} {file}", shell=True)
            return self.framescount/totalTime

    # Launches the video recording function using a thread
    def start(self):
        self.th = Thread(target=self.record)
        self.th.start()


def reFFMPEG(iFile, ifFPS, oFile, oFPS):
    # change fps of the video file
    subprocess.call(f"ffmpeg -r {ifFPS} -i {iFile} -r {oFPS} {oFile}", shell=True)



# def reMoviePy(iFile, oFile, fps=15):
#     my_clip = mpe.VideoFileClip(iFile)
#     my_clip.write_videofile(oFile,fps)



def mergeFFMPEG(videoStream, audioStream, videoOut):
    subprocess.call(f"ffmpeg -ac 2 -channel_layout stereo -i {videoStream} -i {audioStream} {videoOut}", shell=True)



# def mergeMoviePy(videoStream, audioStream, videoOut, fps=15):

#     my_clip = mpe.VideoFileClip(videoStream)
#     audio_background = mpe.AudioFileClip(audioStream)
#     final_clip = my_clip.set_audio(audio_background)
#     final_clip.write_videofile(videoOut,fps)



if __name__ == '__main__':
    # # # os.remove('./output_new.wav')
    ra = AudioRecorder()
    rv = VideoRecorder()

    filev = f"Video_{timeStamp()}.avi"
    filea = f"Audio_{timeStamp()}.wav"
    # ra.start()

    rv.start()
    sleep(5)
    # ra.stop(filea)
    fps = rv.stop(filev)

    # reFFMPEG(filev, fps, 'out.mp4', rv.fps)

    # mergeFFMPEG('out.mp4', filea, 'outfinal.mp4')

    # mergeMoviePy(filev,filea,'outmvpy.mp4',rv.fps)
