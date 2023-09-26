# import os
# import tempfile

# import speech_recognition as sr
# from pydub import AudioSegment

# # Create a recognizer instance


# class GoogleTranscriber:
#     supported_filetypes = ['mp3', 'wav']

#     def __init__(self):
#         self.recognizer = sr.Recognizer()

#     def transcribe(self, filepath, filetype):
#         if filetype not in self.supported_filetypes:
#             raise ValueError(
#                 f'Filetype {filetype} not supported. '
#                 f'Supported file types are {self.supported_filetypes}.'
#             )
#         if filetype != 'wav':
#             with tempfile.NamedTemporaryFile(suffix='.wav') as tmp:
#                 self.convert(source=filepath, destination=tmp.name)
#                 return self.transcribe_wav(tmp.name)
#         self.transcribe_wav(filepath)

#     def convert(self, source, destination):
#         # Ref: https://pythonbasics.org/convert-mp3-to-wav/
#         # TODO: Check supporting format and handle error if format not supported
#         source_format = os.path.splitext(source)[1].strip('.')
#         destination_format = os.path.splitext(destination)[1].strip('.')
#         sound = AudioSegment.from_file(source, source_format)
#         sound.export(destination, format=destination_format)

#     def transcribe_wav(self, filename_or_fileobject):
#         """
#         Supports WAV/AIFF/FLAC audio file.  
#         Returns string.
#         """
#         with sr.AudioFile(filename_or_fileobject) as source:
#             try:
#                 # Adjust the ambient noise threshold if necessary
#                 self.recognizer.adjust_for_ambient_noise(source)

#                 # Capture the audio input from the microphone
#                 audio = self.recognizer.listen(source)

#                 # Perform speech recognition
#                 result = self.recognizer.recognize_google(audio)

#                 # Print the real-time transcription
#                 return result

#             except sr.UnknownValueError as e:
#                 # Speech was unintelligible
#                 print("Unable to recognize speech.")

#             except sr.RequestError as e:
#                 # Error occurred during recognition
#                 print(f"Error: {e}")
