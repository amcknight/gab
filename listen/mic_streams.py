import pyaudio
from six.moves import queue


class ResumableMicrophoneStream:
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self, rate, chunk_size, streaming_limit, start_time):
        self.rate = rate
        self.chunk_size = chunk_size
        self.channels = 1
        self._buff = queue.Queue()
        self.closed = True
        self.start_time = start_time
        self.streaming_limit = streaming_limit
        self.restart_counter = 0
        self.audio_input = []
        self.last_audio_input = []
        self.result_end_time = 0
        self.is_final_end_time = 0
        self.final_request_end_time = 0
        self.bridging_offset = 0
        self.last_transcript_was_final = False
        self.new_stream = True
        self._audio_interface = pyaudio.PyAudio()
        self.format = pyaudio.paInt16
        self.sample_width = self._audio_interface.get_sample_size(self.format)
        self._audio_stream = self._audio_interface.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            # Run the audio stream asynchronously to fill the buffer object. This is necessary so that the input
            # device's buffer doesn't overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

    def __enter__(self):
        self.closed = False
        return self

    def __exit__(self, type_, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, *args, **kwargs):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        """Stream Audio from microphone to API and to local buffer"""
        while not self.closed:
            data = []
            if self.new_stream and self.last_audio_input:
                len_last_input = len(self.last_audio_input)
                chunk_time = self.streaming_limit / len_last_input
                if chunk_time != 0:
                    if self.bridging_offset < 0:
                        self.bridging_offset = 0
                    if self.bridging_offset > self.final_request_end_time:
                        self.bridging_offset = self.final_request_end_time
                    chunks_from_ms = round((self.final_request_end_time - self.bridging_offset) / chunk_time)
                    self.bridging_offset = round((len_last_input - chunks_from_ms) * chunk_time)
                    for i in range(chunks_from_ms, len_last_input):
                        data.append(self.last_audio_input[i])
                self.new_stream = False

            # Use a blocking get() to ensure there's at least one chunk of data, and stop iteration if the chunk is
            # None, indicating the end of the audio stream.
            chunk = self._buff.get()
            self.audio_input.append(chunk)

            if chunk is None:
                return
            data.append(chunk)

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                    self.audio_input.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)
