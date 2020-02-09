
import glob
import os
import logging
import time
import subprocess
import signal
import psutil
import re



##PROCESS (ANALYSIS TYPE)
processName = 'NL41'

username = 'ARCADIS\\kraczlam5898'

## PATH TO THE DIR & FILE CONTAINING A BATCH FILE.
## NOTE: THE FORMAT OF THE 'commands.bat' FILE IS SPECIFIC.
PATH_COMMANDS = r'D:\user\kraczlam5898\Utils'


## PATH TO THE DIR CONTAINING .dat .dcf FILES.
PATH_MODEL = r'E:\user\kraczlam5898\Shear beam'

## SEARCHED PHRASES IN THE .OUT FILE
rx_dict = {
    'conv': re.compile(r'\s*STEP\s*(?P<step_n>\d*)\s*TERMINATED,\s*CONVERGENCE\s*AFTER\s*(?P<itera>\d*)\s*ITERATION(S)?'),
    'not_conv': re.compile(r'\s*STEP\s*(?P<step_n>\d*)\s*TERMINATED,\s*NO\s*CONVERGENCE\s*AFTER\s*(?P<itera>\d*)\s*ITERATION(S)?')
    ''
    }
    
## LIST OF ANALYSES (BAT FILES WITH DIANA COMMANDS)
listOfAnalysis = ['LB6.bat', 'LB61.bat']


numUnconvSteps = 3



def findProcessIdByName(processName, username):
    '''
    Get a list of all the PIDs of a all the running process whose name contains
    the given string processName
    '''
 
    listOfProcessObjects = []
 
    #Iterate over the all the running process
    for proc in psutil.process_iter():
       try:
           pinfo = proc.as_dict(attrs=['pid', 'name', 'create_time', 'username'])
           # Check if process name contains the given name string.
           if processName.lower() in pinfo['name'].lower() and username.lower() in pinfo['username'].lower():
               listOfProcessObjects.append(pinfo)
       except (psutil.NoSuchProcess, psutil.AccessDenied , psutil.ZombieProcess) :
           pass
    return listOfProcessObjects



def printProcessInfo(processes):
    if len(listOfProcessIds) > 0:
       print('Process Exists | PID and other details are')
       for elem in listOfProcessIds:
           processID = elem['pid']
           processName = elem['name']
           processCreationTime =  time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(elem['create_time']))
           processUserame = elem['username']
           print((processID , processName, processUserame, processCreationTime ))
           return (processID , processName, processUserame, processCreationTime )
    else :
       print('No Running Process found with given text')



def parseLines(line):
    for key, rx in rx_dict.items():
        match = rx.search(line)
        if match:
            return key, match
    return None, None



def follow(file):
    '''
    Generator reads one line at the time from the end of the file
    '''

    file.seek(0,2)
    while True:
        line = file.readline()
        if not line:
            time.sleep(0.1)
            continue
        yield line
    
    
    
def terminationCriteria(stepsArr, numLastSteps):
    '''
    Specifies the conditions to terminate the analysis.
    Hereunder, the analysis is set to terminate when a series of consecutive 
    load steps equal to numLastSteps is not converged
    
    Other conditions can be also added. 
    '''
    
    lastNSteps = stepsArr[-numLastSteps:]
    if all([not i for i in lastNSteps]):
        return True
    return False

    

def appendResults(key, matchObj):
    '''
    Outputs results from match objects: 
    if a load step is converged append True; else False
    '''
    
    step_number = int(matchObj.group('step_n'))
    iterations = int(matchObj.group('itera'))
    allStepsIterations.append(iterations)
    
    if key == 'conv':
        convergenceSteps.append(True)
        logging.info("Step {} converged after {}".format(step_number, iterations))
    else:
        convergenceSteps.append(False)
        logging.info("Step {} not converged after {}".format(step_number, iterations))
        
        
def createCommands(batFile):
    f = open('commands.bat', 'r')
    lines = f.readlines()[:-1]
    f.close()

    f = open('commands.bat', 'w')
    for line in lines:
        f.write(line)

    f.write(batFile)
    f.close()
    
    
def initSubprocess():
    assert os.getcwd() == PATH_COMMANDS, ""
    process = subprocess.Popen(["commands.bat"], shell=True )
    return process
    

def openOutFile(analysisName):
    numSec = 10
    timeout = time.time() + numSec
    while True:
    try:
        outFile = open(analysisName + ".out", "r")
        print(outFile)
        if outFile:
            return outFile
    except OSError:
        print (".out file not found.")
    finally:
        if time.time() > timeout:
            raise OSError
    

    
for file in listOfAnalysis:

    os.chdir(PATH_COMMANDS)
    createCommands(file)
    analysisName = file.split(".")[0] + "_test"
    
    process = initSubprocess()
           
    os.chdir(PATH_MODEL)

    convergenceSteps = []
    allStepsIterations = []

    outFile = openOutFile(analysisName)
            
    loglines = follow(outFile)

    
    logging.basicConfig(filename='logfile.log', level=logging.DEBUG, format='%(asctime)s:%(message)s')

    with open('logfile.log', 'w'):
        t_1 = time.time()
        logging.info("beginning of calculations/loop for {}".format(analysisName))
        pass
        

        
        
    for line in loglines:
        if processName in line:
            listOfProcessIds = findProcessIdByName(processName, username)
            processInfo = printProcessInfo(listOfProcessIds)
            currPId = listOfProcessIds[0]['pid']
            print (currPId)
            
            logging.info(str(processInfo))
            logging.info("current PId {}".format(currPId))
            
        key, match = parseLines(line)
        
        if match:
            appendResults(key, match)
            print(convergenceSteps)
            print(allStepsIterations)

            
        if terminationCriteria(convergenceSteps, numUnconvSteps) and len(convergenceSteps) >= numUnconvSteps:
                logging.info("ENDING THE ANALYSIS. \n PROCESS {} IS BEING TERMINATED".format(currPId))
                process = psutil.Process(currPId)
                process.terminate()
                t_2 = time.time() - t_1
                t_2 = divmod(t_2, 60)
                logging.info("end of calculations/loop. Loop time: {}".format(t_2))

                break
      


            