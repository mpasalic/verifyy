
# # # # # # # # # # # # # # # # # # # # 
# This is a conversion utlity thing:
#   Data representation of everying is
#   a floating-point number, but we need
#   to handle input / output conversion of data
#

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
        #TODO: IMPLEMENT TIME INPUT CONVERSION
        ass = 1/0
