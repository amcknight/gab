import re
import sys
import tempfile

import time
import wave
from google.cloud import speech
from listen.mic_streams import ResumableMicrophoneStream

# Audio recording parameters
STREAMING_LIMIT = 4*60*1000
SAMPLE_RATE = 44100
CHUNK_SIZE = int(SAMPLE_RATE / 10)  # 100ms

RED = "\033[0;31m"
YELLOW = "\033[0;33m"
GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
WHITE = "\033[0;37m"


def now():
    return int(round(time.time() * 1000))


def listen():
    """start bidirectional streaming from microphone input to speech API"""
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=SAMPLE_RATE,
        language_code="en-US",
        max_alternatives=1,
        enable_automatic_punctuation=True,
    )
    streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)
    listen_with(streaming_config, single_print_loop)


def multi_listen():
    """start bidirectional streaming from microphone input to speech API"""
    diarization_config = speech.SpeakerDiarizationConfig(
        enable_speaker_diarization=True,
        min_speaker_count=2,
        max_speaker_count=10,
    )
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=SAMPLE_RATE,
        language_code="en-US",
        max_alternatives=1,
        enable_automatic_punctuation=True,
        diarization_config=diarization_config,
        model="video"
    )
    streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)
    listen_with(streaming_config, multi_print_loop)


def listen_with(streaming_config, print_loop):
    client = speech.SpeechClient()
    mic_manager = ResumableMicrophoneStream(SAMPLE_RATE, CHUNK_SIZE, STREAMING_LIMIT, now())
    sys.stdout.write(YELLOW)
    sys.stdout.write('\nListening, say "Quit" or "Exit" to stop.\n\n')
    sys.stdout.write("End (ms)       Transcript Results/Status\n")
    sys.stdout.write("=====================================================\n")

    filename = tempfile.mktemp(prefix='temp_', suffix='.wav', dir='')

    with mic_manager as stream, wave.open(filename, 'wb') as wav:
        _configure_wave_file(wav, mic_manager)
        while not stream.closed:
            sys.stdout.write(YELLOW)
            sys.stdout.write("\n" + str(STREAMING_LIMIT * stream.restart_counter) + ": NEW REQUEST\n")

            stream.audio_input = []
            audio_generator = stream.generator()

            def do_stuff(content):
                wav.writeframes(content)
                return speech.StreamingRecognizeRequest(audio_content=content)

            requests = (
                do_stuff(content) for content in audio_generator
            )
            responses = client.streaming_recognize(streaming_config, requests)

            # Now, put the transcription responses to use.
            print_loop(responses, stream)

            if stream.result_end_time > 0:
                stream.final_request_end_time = stream.is_final_end_time
            stream.result_end_time = 0
            stream.last_audio_input = []
            stream.last_audio_input = stream.audio_input
            stream.audio_input = []
            stream.restart_counter += 1

            if not stream.last_transcript_was_final:
                sys.stdout.write("\n")
            stream.new_stream = True


def single_print_loop(responses, stream):
    """Iterates through server responses and prints them.

    The responses passed is a generator that will block until a response is provided by the server.

    Each response may contain multiple results, and each result may contain multiple alternatives; for details,
    see https://goo.gl/tjCPAU. Here we print only the transcription for the top alternative of the top result.

    In this case, responses are provided for interim results as well. If the response is an interim one, print a line
    feed at the end of it, to allow the next result to overwrite it, until the response is a final one. For the final
    one, print a newline to preserve the finalized transcription.
    """
    for response in responses:
        if now() - stream.start_time > STREAMING_LIMIT:
            stream.start_time = now()
            break
        if not response.results:
            continue
        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript

        result_seconds = 0
        result_micros = 0

        if result.result_end_time.seconds:
            result_seconds = result.result_end_time.seconds

        if result.result_end_time.microseconds:
            result_micros = result.result_end_time.microseconds

        stream.result_end_time = int((result_seconds * 1000) + (result_micros / 1000))

        corrected_time = stream.result_end_time - stream.bridging_offset + (STREAMING_LIMIT * stream.restart_counter)

        # Display interim results with a carriage return at the end of line, so subsequent lines will overwrite them.
        if result.is_final:
            sys.stdout.write(GREEN)
            sys.stdout.write("\033[K")
            sys.stdout.write(str(corrected_time) + ": " + transcript + "\n")

            stream.is_final_end_time = stream.result_end_time
            stream.last_transcript_was_final = True

            # Exit recognition if any of the transcribed phrases could be one of our keywords.
            if re.search(r"\b(exit|quit)\b", transcript, re.I):
                sys.stdout.write(YELLOW)
                sys.stdout.write("Exiting...\n")
                stream.closed = True
                break

        else:
            sys.stdout.write(RED)
            sys.stdout.write("\033[K")
            sys.stdout.write(str(corrected_time) + ": " + transcript + "\r")

            stream.last_transcript_was_final = False


def multi_print_loop(responses, stream):
    """Iterates through server responses and prints them.

    The responses passed is a generator that will block until a response is provided by the server.

    Each response may contain multiple results, and each result may contain multiple alternatives; for details,
    see https://goo.gl/tjCPAU. Here we print only the transcription for the top alternative of the top result.

    In this case, responses are provided for interim results as well. If the response is an interim one, print a line
    feed at the end of it, to allow the next result to overwrite it, until the response is a final one. For the final
    one, print a newline to preserve the finalized transcription.
    """
    for response in responses:
        if now() - stream.start_time > STREAMING_LIMIT:
            stream.start_time = now()
            break
        if not response.results:
            continue
        result = response.results[0]
        if not result.alternatives:
            continue

        result_seconds = 0
        result_micros = 0
        if result.result_end_time.seconds:
            result_seconds = result.result_end_time.seconds
        if result.result_end_time.microseconds:
            result_micros = result.result_end_time.microseconds
        stream.result_end_time = int((result_seconds * 1000) + (result_micros / 1000))
        corrected_time = stream.result_end_time - stream.bridging_offset + (STREAMING_LIMIT * stream.restart_counter)

        transcript = result.alternatives[0].transcript
        speaker = '?'

        # Display interim results with a carriage return at the end of line, so subsequent lines will overwrite them.
        if result.is_final:
            sys.stdout.write(WHITE)
            sys.stdout.write("\033[K")
            sys.stdout.write(str(corrected_time) + ": ")
            for words in result.alternatives[0].words:
                word = words.word
                match words.speaker_tag:
                    case 1: sys.stdout.write(GREEN)
                    case 2: sys.stdout.write(BLUE)
                    case _: sys.stdout.write(WHITE)
                sys.stdout.write(word + " ")
            sys.stdout.write("\n")

            stream.is_final_end_time = stream.result_end_time
            stream.last_transcript_was_final = True
            sys.stdout.write(WHITE)

            # Exit recognition if any of the transcribed phrases could be one of our keywords.
            if re.search(r"\b(exit|quit)\b", transcript, re.I):
                sys.stdout.write(YELLOW)
                sys.stdout.write("Exiting...\n")
                stream.closed = True
                break

        else:
            sys.stdout.write(RED)
            sys.stdout.write("\033[K")
            sys.stdout.write(speaker + "> " + str(corrected_time) + ": " + transcript + "\r")

            stream.last_transcript_was_final = False


def _configure_wave_file(wav, mic_manager):
    wav.setnchannels(mic_manager.channels)
    wav.setsampwidth(mic_manager.sample_width)
    wav.setframerate(mic_manager.rate)
