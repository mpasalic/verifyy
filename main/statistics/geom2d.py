# # # # # # # # # # # # # # # # #
# @author Alexander Novikov
#
# Some basic geometry definitions for the state-of-the-art
# custering algorithm
#

import math

class point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
    def distanceTo(self, pointOther):
        dx = (self.x - pointOther.x)
        dy = (self.y - pointOther.y)
        return math.sqrt(dx * dx + dy * dy)
        
    def __str__(self):
        return "(%.2f,%.2f)" % (self.x,self.y)


class cluster(object):
    def __init__(self):
        self.points = []
        self.sumFy = 0
        self.sumFx = 0
        self.sumxy = 0
    
    def centroid(self):
        #thisCentroid = point(float(self.sumxy)/self.sumFx, float(self.sumxy)/self.sumFy)
        #return thisCentroid
        thisCentroid = point(float(self.sumFy)/len(self.points),float(self.sumFx)/len(self.points))
        return thisCentroid
    
    def stddev_x(self):
        xbar = float(self.sumFy) / len(self.points)
        sigmaX = 0
        for point in self.points:
            sigmaX += (point.x - xbar)*(point.x - xbar)
        return sigmaX
    
    def stddev_y(self):
        ybar = float(self.sumFx) / len(self.points)
        sigmaY = 0
        for point in self.points:
            sigmaY += (point.y - ybar)*(point.y - ybar)
        return sigmaY
    
    def stddev_xy(self):
        return max(self.stddev_x(), self.stddev_y())
    
    def addPoint(self, pt):
        self.points.append(pt)
        self.sumFx += pt.y
        self.sumFy += pt.x
        self.sumxy += pt.y * pt.x
    
    def xcentroidDistanceTo(self, othr):
        thisCentroid = point(float(self.sumxy)/self.sumFx, 0)
        thatCentroid = point(float(othr.sumxy)/othr.sumFx, 0)
        return thisCentroid.distanceTo(thatCentroid)
        
    def centroidDistanceTo(self, othr):
        c_x = 0.0
        c_y = 0.0
        o_x = 0.0
        o_y = 0.0
        if (self.sumxy != 0 or self.sumFx != 0):
            c_x = float(self.sumxy)/self.sumFx
        if (self.sumxy != 0 or self.sumFy != 0):
            c_y = float(self.sumxy)/self.sumFy
        if (othr.sumxy != 0 or othr.sumFx != 0):
            o_x = float(othr.sumxy)/othr.sumFx
        if (othr.sumxy != 0 or othr.sumFy != 0):
            o_y = float(othr.sumxy)/othr.sumFy
        
        thisCentroid = point(c_x, c_y)
        thatCentroid = point(o_x, o_y)
        return thisCentroid.distanceTo(thatCentroid)
        
    def maxDistanceTo(self, clusterOther):
        best = 0
        #TODO: add better optimization here
        for point1 in self.points:
            for point2 in clusterOther.points:
                dist = point1.distanceTo(point2)
                if dist > best:
                    best = dist
        return best

    def minDistanceTo(self, clusterOther):
        best = float(1<<31)
        #TODO: add better optimization here
        for point1 in self.points:
            for point2 in clusterOther.points:
                dist = point1.distanceTo(point2)
                if dist < best:
                    best = dist
        return best
    
    def distanceTo(self, clusterOther):
        return self.centroidDistanceTo(clusterOther)    
    
    def __str__(self):
        return "[" + ", ".join(map(lambda p: str(p), self.points)) + "]"


