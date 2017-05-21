from core.subprocesslauncher import Subprocesslauncher
import sys
import os

def checkandconvert():
    #Paths and make sure they exist
    path_to_python = sys.executable
    path_of_script = os.path.dirname(os.path.realpath(__file__))
    nzbtomediadirectory = os.path.abspath(os.path.join(path_of_script,os.pardir))
    coredir = os.path.abspath(os.path.join(nzbtomediadirectory,'core'))
    path_of_checkfilesandfolderpy = os.path.abspath(os.path.join(nzbtomediadirectory,'checkfilesinfolder.py'))
    path_of_sickbeard_mp4_autommator = os.path.abspath(os.path.join(nzbtomediadirectory,'sickbeard_mp4_automator','manual.py'))
    if not (os.path.isfile(path_of_checkfilesandfolderpy) and os.path.isfile(path_of_sickbeard_mp4_autommator) and os.path.exists(nzbtomediadirectory)):
        print('not all files present')
        print('I am going to crash with an evil exception')
        sys.exit(1)

    #Standardanswer for convertion == 1 #failed
    answerconvertion = 1
    folder = sys.argv[1]
    checkfilesinfolder_py = Subprocesslauncher(path_to_python, path_of_checkfilesandfolderpy, sys.argv[1:],terminalprefix='<<<< FILECHECK >>>>  ',readmethod=3)
    converterpythonfile = Subprocesslauncher(path_to_python,path_of_sickbeard_mp4_autommator,['-a','-i',folder],terminalprefix='<<<< CONVERTER >>>>  ',readmethod=3)

    #Launch Filechecking and get the exit code
    answerchecks = checkfilesinfolder_py.launch()

    if answerchecks == 0:
        for i in range(0,2):
            while answerconvertion != 0:
                answerconvertion = converterpythonfile.launch()
                break
        if answerconvertion != 0:
            print('convertion failed')
            sys.exit(1)
        else:
            print('convertions okay')
            return answerconvertion
    else:
        print('The check of the main files failed, so no convertion is taking place and failedstate is given back')
        return answerchecks

if __name__ == '__main__':
    exit(checkandconvert())