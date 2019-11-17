from core.checkandconvertbysickbeardmp4conv import checkandconvert
from core.subprocesslauncher import Subprocesslauncher
import os
import sys

def main():
    # Paths and make sure they exist
    path_to_python = sys.executable
    path_of_script = os.path.dirname(os.path.realpath(__file__))
    nzbtomediadirectory = os.path.abspath(os.path.join(path_of_script))
    path_of_nzbtosickbeardpy = os.path.abspath(os.path.join(nzbtomediadirectory,'nzbToNzbDrone.py'))
    if not (os.path.isfile(path_of_nzbtosickbeardpy) and os.path.exists(nzbtomediadirectory)):
        print('not all files present')
        print('I am going to crash with an evil exception')
        sys.exit(1)

    #Runs checkandconvert Files are checked and converted to mp4 the return value is given back afterwards
    answer = checkandconvert()
    postprocessing = Subprocesslauncher(path_to_python,path_of_nzbtosickbeardpy,sys.argv[1:],terminalprefix='NZBTOSONARR    ')
    answerpostprocessing = postprocessing.launch()

    return answerpostprocessing

if __name__ == '__main__':
    exit(main())