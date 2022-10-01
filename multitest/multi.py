import io
from multitest import ear
from multitest import example
import sounddevice as sd
from google.cloud import speech_v1p1beta1 as speechtotext


class Multi:
    def __init__(self):
        # self.mp3Path = './multitest/conversation.mp3'
        # self.client = speechtotext.SpeechClient()

        # audio = ear.FlacAudioStream()
        # audio.stream.start()
        # audio.listen()

        example.main()

    def speech_to_text(self):
        config = speechtotext.RecognitionConfig({
            'encoding': speechtotext.RecognitionConfig.AudioEncoding.MP3,
            'sample_rate_hertz': sd.default.samplerate,
            'language_code': 'en-US',
            'enable_automatic_punctuation': True,
            'enable_speaker_diarization': True,
            'diarization_speaker_count': 2,
            'model': 'phone_call'
        })
        with io.open(self.mp3Path, "rb") as f:
            content = f.read()
        audio = speechtotext.RecognitionAudio({"content": content})

        results = self.client.recognize(config=config, audio=audio).results
        if len(results) < 1:
            return None
        id_words = []
        for result in results:
            for alternative in result.alternatives:
                for words in alternative.words:
                    if words.speaker_tag:
                        id_words.append((words.speaker_tag, words.word))
        id_lines = []
        (last_id, _) = id_words[0]
        last_line = ""
        for (speaker_id, word) in id_words:
            if speaker_id == last_id:
                last_line += " " + word
            else:
                id_lines.append((last_id, last_line))
                last_id = speaker_id
                last_line = word
        return id_lines
