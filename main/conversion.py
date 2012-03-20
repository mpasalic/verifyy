# # # # # # # # # # # # # # # # # # # # 
# @author Alexander Novikov
#
# This is a conversion utlity thing:
#   Data representation of everying is
#   a floating-point number, but we need
#   to handle input / output conversion of data
#

import time
import calendar

from main.models import Data

TIME_PARSE_FMT="%Y-%m-%d %H:%M:%S %Z"

# Do not change the relative ordering of associated
# constants:
#
#   NO_FOLD < HOURLY < DAILY < WEEKLY
#
class TIME_FOLDING:
    NO_FOLD = 0
    HOURLY  = 1
    DAILY   = 2
    WEEKLY  = 3
    
    SECONDS_IN_HOUR = 60 * 60
    SECONDS_IN_DAY =  24 * SECONDS_IN_HOUR
    
    def strValueOf(self, enumVal):
        if enumVal == self.NO_FOLD:
            return "None"
        elif enumVal == self.HOURLY:
            return "Hourly"
        elif enumVal == self.DAILY:
            return "Daily"
        elif enumVal == self.WEEKLY:
            return "Weekly"
        raise KeyError("Not a valid TIME_FOLDING constant")

def parseTypeOrError(val, type, mapping=None):
    if type == 'c':
        # This is a enum-value, need to validate it
        # on error simply throws KeyError
        valT = int(val)
        if valT in mapping:
            return valT
        else:
            raise KeyError("Unexpected enum value (%s)" % valT)
    if type == 'r':
        # This is a real number, so just take it as it is
        return float(val)
    if type == 't':
        #Here, assume the time is in datetime format
        dataTime = time.strptime(val, TIME_PARSE_FMT)
        #Convert it to number of seconds since epoch and shove it in as float
        seconds = calendar.timegm(dataTime)
        return seconds

# This function is used to take care of site's internal time
# float-value representation and fold it to an appropriate interval
# 

def foldTime(val, period):
    # We may not want to fold time is certain circumstances
    if period == TIME_FOLDING.NO_FOLD:
        return val
    
    dataTime = time.gmtime(val)
    converted = 0
    if period >= TIME_FOLDING.HOURLY:
        converted += dataTime.tm_min * 60 + dataTime.tm_sec
    if period >= TIME_FOLDING.DAILY:
        converted += TIME_FOLDING.SECONDS_IN_HOUR * dataTime.tm_hour
    if period >= TIME_FOLDING.WEEKLY:
        theDayOfWeek = calendar.weekday(dataTime.tm_year, dataTime.tm_mon, dataTime.tm_mday)
        converted += TIME_FOLDING.SECONDS_IN_DAY * theDayOfWeek
    
    return converted

# # # # # # # # # # # # # # # # # # # #
# 
# Simply run it over data points
# But do NOT save the modified data pts!
#
def convertTimeByFolding(datas, period):
    if (period == None) or (period == TIME_FOLDING.NO_FOLD):
        return
    
    for data in datas:
        data.x = foldTime(data.x, period)
    return
    