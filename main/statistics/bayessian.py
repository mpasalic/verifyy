from main.statistics.common import Analysis

# SimpleBayessianAnalysis:
#   We have a collection of observations, x & y are discrete
#
#   TODO:
#   We can compare probabilities of P(Y_j | X_i) and use it 
#       as error measure.
#
class SimpleBayessianAnalysis(Analysis):

    def __init__(self, classesX, classesY):
        super(SimpleBayessianAnalysis, self).__init__()
        # Intialize a table of level to points for that level
        self.table = {}
        self.classesX = classesX
        self.classesY = classesY
        for clsX in classesX:
            self.table[clsX] = {}
            for clsY in classesY:
                self.table[clsX][clsY] = 0
    
    def analyse(self, data):
        # record the discrete data into the correct bin
        for datum in data:
            self.table[datum.x][datum.y] += 1
        
        #TODO: DO FURTHER ANALYSIS
        
        pass