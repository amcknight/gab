import queue
import pyflac
import sounddevice as sd
from google.cloud import speech


class FlacAudioStream:
    def __init__(self):
        self.rate = 44100
        self.stream = sd.InputStream(dtype='int16', callback=self.audio_callback, samplerate=self.rate)
        self.encoder = pyflac.StreamEncoder(write_callback=self.encoder_callback, sample_rate=self.rate)
        self.queue = queue.SimpleQueue()
        self.client = speech.SpeechClient()

    def audio_callback(self, indata, frames, sd_time, status):
        # print(indata)
        self.encoder.process(indata)

    def encoder_callback(self, buffer, num_bytes, num_samples, current_frame):
        # print(buffer)
        self.queue.put(buffer)

    def listen(self):
        config = speech.RecognitionConfig({
            'encoding': speech.RecognitionConfig.AudioEncoding.FLAC,
            'sample_rate_hertz': self.rate,
            'language_code': 'en-US',
            'max_alternatives': 1
        })
        streaming_config = speech.StreamingRecognitionConfig({'config': config})
        responses = self.client.streaming_recognize(streaming_config, self.request_generator())
        print(responses)
        for response in responses:
            # Once the transcription has settled, the first result will contain the is_final result.
            # The other results will be for subsequent portions of the audio.
            for result in response.results:
                print("Finished: {}".format(result.is_final))
                print("Stability: {}".format(result.stability))
                alternatives = result.alternatives
                # The alternatives are ordered from most likely to least.
                for alternative in alternatives:
                    print("Confidence: {}".format(alternative.confidence))
                    print(u"Transcript: {}".format(alternative.transcript))

    def request_generator(self):
        # yield speech.StreamingRecognizeRequest({'streaming_config': streaming_config})
        while True:
            chunk = self.queue.get()
            yield speech.StreamingRecognizeRequest(audio_content=chunk)

# import sounddevice as sd
# import soundfile as sf
# import queue
# import sys
# import tempfile
# import numpy as np
# from google.cloud import speech as speech
#
# rate = 44100
# channels = 2
# sd.default.samplerate = rate
# sd.default.channels = channels
#
# q = queue.Queue()
#
# client = speech.SpeechClient()
#
#
# def callback(indata, frames, time, status):
#     """This is called (from a separate thread) for each audio block."""
#     if status:
#         print(status, file=sys.stderr)
#     print("INDATA:")
#     volume_norm = np.linalg.norm(indata) * 10
#     print(int(volume_norm))
#     # print(time.inputBufferAdcTime, time.outputBufferDacTime, time.currentTime)
#     q.put(indata.copy())
#
#
# def record():
#     filename = tempfile.mktemp(prefix='delme_rec_unlimited_', suffix='.wav', dir='')
#     try:
#         # Make sure the file is opened before recording anything:
#         with sf.SoundFile(filename, mode='x', samplerate=rate, channels=channels) as file:
#             with sd.InputStream(samplerate=rate, channels=channels, callback=callback):
#                 print('#' * 80)
#                 print('press Ctrl+C to stop the recording')
#                 print('#' * 80)
#                 while True:
#                     chunk = q.get()
#                     file.write(chunk)
#                     handle_sound(chunk)
#     except KeyboardInterrupt:
#         print('\nRecording finished: ' + repr(filename))
#         exit(0)
#
#
# def handle_sound(chunk):
#     config = speech.RecognitionConfig({
#         'encoding': speech.RecognitionConfig.AudioEncoding.LINEAR16,
#         'sample_rate_hertz': sd.default.samplerate,
#         'language_code': 'en-US',
#         'enable_automatic_punctuation': True
#     })
#
#     streaming_config = speech.StreamingRecognitionConfig({'config': config})
#     requests = [
#         speech.StreamingRecognizeRequest({'streaming_config': streaming_config}),
#         speech.StreamingRecognizeRequest({'audio_content': chunk})
#     ]
#     responses = client.streaming_recognize(requests)
#     print(responses)
#     exit(100)
#     for response in responses:
#         # Once the transcription has settled, the first result will contain the is_final result.
#         # The other results will be for subsequent portions of the audio.
#         for result in response.results:
#             print("Finished: {}".format(result.is_final))
#             print("Stability: {}".format(result.stability))
#             alternatives = result.alternatives
#             # The alternatives are ordered from most likely to least.
#             for alternative in alternatives:
#                 print("Confidence: {}".format(alternative.confidence))
#                 print(u"Transcript: {}".format(alternative.transcript))
