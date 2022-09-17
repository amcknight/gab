#!/usr/bin/env python3

import time
import pyaudio
import wave
import sched
import secrets
import pydub
import io
from playsound import playsound
from google.cloud import speech_v1p1beta1 as speech


class Capture:
    def __init__(self):
        self.CHUNK = 8192
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.RECORD_SECONDS = 5
        self.HEX = secrets.token_hex(4)

        self.p = pyaudio.PyAudio()
        self.frames = []

        self.capturing = False
        self.started = False
        self.last_text = None
        self.stream = None
        self.wf = None

        self.client = speech.SpeechClient()
        self.recording_index = 0
        self.task = sched.scheduler(time.time, time.sleep)

    def run(self):
        self.task.enter(0.05, 1, self.recorder, ())
        self.task.run()

    def on(self):
        self.capturing = True

    def off(self):
        self.capturing = False

    def callback(self, in_data, _frame_count, _time_info, _status):
        self.frames.append(in_data)
        return in_data, pyaudio.paContinue

    def output_name(self, ext):
        return "out-" + self.HEX + "-" + str(self.recording_index) + "." + ext

    def again(self):
        self.task.enter(0.05, 1, self.recorder, ())

    def recorder(self):
        if self.capturing and not self.started:
            self.started = True
            self.recording_index += 1
            self.wf = wave.open(self.output_name("wav"), 'wb')
            self.wf.setnchannels(self.CHANNELS)
            self.wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
            self.wf.setframerate(self.RATE)
            self.stream = self.p.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, input=True,
                                      frames_per_buffer=self.CHUNK, stream_callback=self.callback)
            self.again()

        elif not self.capturing and self.started:
            self.started = False
            self.stream.stop_stream()
            self.stream.close()
            self.wf.writeframes(b''.join(self.frames))
            self.wf.close()

            sound = pydub.AudioSegment.from_wav(self.output_name("wav"))
            sound.export(self.output_name("mp3"), format="mp3")

            results = self.sample_recognize(self.output_name("mp3"))
            if len(results) == 0:
                playsound("room/resources/ding.mp3")
                self.again()
            else:
                for result in results:
                    self.last_text = result.alternatives[0].transcript
                    break
        else:
            self.again()

    def sample_recognize(self, file_path):
        config = speech.RecognitionConfig({
            'encoding': speech.RecognitionConfig.AudioEncoding.MP3,
            'sample_rate_hertz': self.RATE,
            'language_code': 'en-US',
            'enable_automatic_punctuation': True
        })
        with io.open(file_path, "rb") as f:
            content = f.read()
        audio = speech.RecognitionAudio({"content": content})

        return self.client.recognize(config=config, audio=audio).results
