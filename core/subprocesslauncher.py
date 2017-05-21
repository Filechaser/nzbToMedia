import subprocess
import sys
import time
import io

class Subprocesslauncher:
    #input strings of executable and Parameters
    #output returnvalue of Programm run
    def __init__(self, executable='', firstarg='', otherargs=[],readmethod=3,terminalprefix='>>>'):
        self.executable = executable
        self.firstarg = firstarg
        self.otherargs = otherargs
        self.terminalprefix = terminalprefix
        self.readmethod = readmethod

    def launch(self):
        #3 Readmethod 3 Standard with Files in Folder
        if self.readmethod == 3:
            filename = 'stdouttemp.log'
            with io.open(filename, 'wb') as writer, io.open(filename, 'rb', 1) as reader:
                p = subprocess.Popen([self.executable, self.firstarg] + self.otherargs, stdout=writer,stderr=writer)
                while p.poll() is None:
                    sys.stdout.write(reader.read())
                    time.sleep(0.5)
                # Read the remaining
                sys.stdout.write(reader.read())

        #2. Methods to read the Terminal is buggy but working on Windows
        #1. Method  is standard Linuxstyle
        elif self.readmethod == 2:
            p = subprocess.Popen([self.executable, self.firstarg] + self.otherargs, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)
            while True:
                line = p.stdout.readline()
                if line != '':
                    # the real code does filtering here
                    print(self.terminalprefix + line.rstrip())
                else:
                    break
        else:
            p = subprocess.Popen([self.executable, self.firstarg] + self.otherargs, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)
            try:
                # Filter stdout
                for line in iter(p.stdout.readline, ''):
                    sys.stdout.flush()
                    # Print status
                    print(self.terminalprefix + line.rstrip())
                    sys.stdout.flush()
            except:
                sys.stdout.flush()


        # Wait until process terminates (without using p.wait())
        while p.poll() is None:
            # Process hasn't exited yet, let's wait some
            print(self.terminalprefix + " Waiting for process to exit and return value")
            time.sleep(1)

        # Get return code from process
        return_code = p.returncode

        #Print Successfulmessage to Terminal
        print(self.terminalprefix + " Execution sucessful") if return_code == 0 else (self.terminalprefix + " Execution failed")

        #return the return_code
        return return_code

if __name__ == '__main__':
    print('This class-file is not ment to be run directly')