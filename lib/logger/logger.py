###############################################################################
#
#       Logger for this project
#
###############################################################################
#
#                                IMPORTS
#
###############################################################################

import datetime
import os

###############################################################################
#
#                                 CLASS
#
###############################################################################

class Logger:
    __instance = None
    currentDatetime = datetime.datetime.now()
    if os.path.isdir('logs') == False:
            os.mkdir('logs')
    logFile = open('logs/' + str(currentDatetime) + '.log', 'a')

    @staticmethod 
    def getInstance():
       if Logger.__instance == None:
          Logger()
       return Logger.__instance
    
    def __init__(self):
       if Logger.__instance != None:
          raise Exception("This class is a singleton!")
       else:
          Logger.__instance = self

###############################################################################
#
#                               FUNCTIONS
#
###############################################################################

    def log(self, option, msg):
        currentTime = datetime.datetime.now()
        optionMsg = "INFO"
        if option == "warn":
            optionMsg = "WARNING"
        elif option == "debug":
            optionMsg = "DEBUG"
        tmp = msg
        # tmp = msg.replace('\n','')
        print(currentTime, ' -- [', optionMsg, ']: ', tmp)
        self.logFile.write(str(currentTime) + ' -- [' + optionMsg + ']: ' + tmp + '\n')
