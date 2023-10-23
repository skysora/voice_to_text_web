import os


UPLOAD_FOLDER = './web/data/signal/'
SPEECH_RESULT_FOLDER = './web/data/speechResult/'
SUMIT_FOLDER = './web/data/submitFile/'
EMOTION_RESULT_FOLDER = './web/data/emotionResult/'
PROCESS_SPEECH_RESULT_FOLDER = './web/data/process_speechResult/'
TEXT_OUTPUT = './web/data/output/'

# Check if the directories exist, and create them if not
for folder in [UPLOAD_FOLDER, SPEECH_RESULT_FOLDER, SUMIT_FOLDER, EMOTION_RESULT_FOLDER,PROCESS_SPEECH_RESULT_FOLDER,TEXT_OUTPUT]:
    if not os.path.exists(folder):
        os.makedirs(folder)