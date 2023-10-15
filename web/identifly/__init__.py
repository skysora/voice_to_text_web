import os


UPLOAD_FOLDER = './data/signal/'
SPEECH_RESULT_FOLDER = './data/speechResult/'
SUMIT_FOLDER = './data/submitFile/'
EMOTION_RESULT_FOLDER = './data/emotionResult/'

# Check if the directories exist, and create them if not
for folder in [UPLOAD_FOLDER, SPEECH_RESULT_FOLDER, SUMIT_FOLDER, EMOTION_RESULT_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)