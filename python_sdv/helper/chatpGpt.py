# ******************************************************************************************************************
# Copyright (c) Robert Bosch GmbH, 2023. All rights reserved.
# The reproduction, distribution and utilization of this document as well as the communication of its contents to
# others without explicit authorization is prohibited. Offenders will be held liable for the payment of damages.
# All rights reserved in the event of the grant of a patent, utility model or design.
# ******************************************************************************************************************
# FileName : chatGpt.py
# Description : Python program to record a message via Microphone and give it as a input to chatGPT and process the output via speaker.
# Author : Sherin Jasper Sudhaker Vincent (MS/ENC3)

import subprocess
import sys
import speech_recognition as sr

def chatGptUsage():
    print("------------------------------------------------------------------")
    print("Usage:python3 <pythonfile> <duration to record a message>(optional)")
    print("Usage Example:python3 chatGpt.py 10")
    print("Default duration to record is 5 sec will be used if it is not specified")
    print("------------------------------------------------------------------")

#Input validation Check
noOfArgsPassed = len(sys.argv)
print("\nINFO : Name of Python script:", sys.argv[0])
if noOfArgsPassed == 2:
    #Arguments passed
    print("\nINFO : Duartion to record data", sys.argv[1])
    durationToRecord = sys.argv[1]
elif noOfArgsPassed < 2:
    print("\nINFO: Default duration to record is used which is 5 sec")
    durationToRecord = 5
else:
    print ("\nERROR : Invalid no of Arguments passed\n")
    chatGptUsage()
    sys.exit(0)

shellCmd = "arecord -d" + str(durationToRecord) + " -t wav recordedMessage.wav"
shellCmdReturn = subprocess.call(shellCmd, shell=True)
if (shellCmdReturn):
    print("\nERROR: failure in processing Shell Command",shellCmd)
    sys.exit(1)
try:
    # initialize the recognizer
    recognizerObj = sr.Recognizer()
    filename = "recordedMessage.wav"
    with sr.AudioFile(filename) as source:
        # listen for the data (load audio to memory)
        loadedRecordedMessageData = recognizerObj.record(source)
        # recognize (convert from speech to text)
        sgptOutput = recognizerObj.recognize_google(loadedRecordedMessageData)
        print(sgptOutput)
        textFileObj = open("sgptOutput.txt", "w")
        textFileObj.write(sgptOutput)
        textFileObj.close()
except sr.RequestError as exceptionObj:
    print("\nERROR: Could not request results of recorded data; {0}".format(exceptionObj,))
    sys.exit(1)
except sr.UnknownValueError:
    print("\nERROR: Unknown Error Occured during recording..Exiting")
    sys.exit(1)
except FileNotFoundError:
    print("ERROR: Recorded File not found..Exiting")
    sys.exit(1)

shellCmdSgpt = f"cat sgptOutput.txt | sgpt --chat BEGSDVDEMO '{sgptOutput}' > sgptresult.txt"
shellCmdSgptReturn = subprocess.call(shellCmdSgpt, shell=True)
if (shellCmdSgptReturn):
    print("\nERROR: failure in processing Shell Command",shellCmdSgpt)
    sys.exit(1)

shellCmdespeak = "espeak-ng -f sgptresult.txt"
shellCmdespeakpopen = subprocess.Popen(shellCmdespeak, shell=True)
shellCmdespeakReturn = shellCmdespeakpopen.wait()
if (shellCmdespeakReturn):
    print("\nERROR: failure in processing Shell Command", shellCmdespeak)
    sys.exit(1)

chatHistoryFile = "BEGSDVDEMO_chat_history.txt"
shellCmdShowHistory = "sgpt --show-chat BEGSDVDEMO >> " + chatHistoryFile
shellCmdShowHistoryReturn = subprocess.call(shellCmdShowHistory, shell=True)
if (shellCmdShowHistoryReturn):
    print("\nERROR: failure in processing Shell Command",shellCmdShowHistory)
    sys.exit(1)

print("INFO: Chat history is available in ",chatHistoryFile)
