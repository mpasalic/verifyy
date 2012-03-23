# # # # # # # # # # # # # # # # # #
# @author Alexander Novikov
#
# Implementations of several parametric curves over a set of control points
# 
#

class parametric_curve(object):
    
    def getControlPointsForCluster(self, cluster, result = []):
        # Check if this cluster is big enough to generate multiple control points
        # OR that it's x-stddev is at least apprimately y-stddev
        #if (len(cluster.points) < 3) or (cluster.stddev_x() < 0.75 * cluster.stddev_y()):
        if True:
            result.append(cluster.centroid())
            return result
        # Do 3 control points: exponentially weighted beginning/end (with end itself weighting 3/4)
        # 1 centroid
        centroid = cluster.centroid()
        EXP      = float(1)/4
        expn     = 1
        cluster.points.sort(lambda p1,p2: cmp(p1.x, p2.x))
        start = point((1-EXP)*cluster.points[ 0].x,(1-EXP)*cluster.points[ 0].y)
        end   = point((1-EXP)*cluster.points[-1].x,(1-EXP)*cluster.points[-1].y)
        for i in range(1, len(cluster.points)):
            expn = expn * EXP
            start.x += expn * cluster.points[   i].x
            start.y += expn * cluster.points[   i].y
            end.x   += expn * cluster.points[-1-i].x
            end.y   += expn * cluster.points[-1-i].y
            result.append(start)
            result.append(centroid)
            result.append(end)
        return result
    
    
    def __init__(self, paramdict):
        indexes = range(0,len(paramdict['clusters']))
        sortedClusters = map( lambda ci: paramdict['clusters'][ci], sorted(indexes, lambda i, j: cmp(paramdict['xmins'][i],paramdict['xmins'][j])) )
        self.controlPoints = []
        for clster in sortedClusters:
            self.getControlPointsForCluster(clster, self.controlPoints)
        
    def evalPoints(self, numpoints):
        results = []
        ppi = int(math.ceil(float(numpoints)/self.nintervals))
        for i in range(0, self.nintervals):
            self.evalInterval(i, ppi, results)
        return results

class bezier_curve(parametric_curve):
    def __init__(self, paramdict):
        super(bezier_curve, self).__init__(paramdict)
        self.nintervals = len(self.controlPoints) - 4
    
    def evalInterval(self, iintrvl, numpoints, results):
        controlPts = self.controlPoints[iintrvl:iintrvl+4]
        for i in range(0, numpoints+1):
            t = float(i)/(numpoints)
            x = (1-t)*(1-t)*(1-t)*controlPts[0].x + 3*(1-t)*(1-t)*t*controlPts[1].x + 3*(1-t)*t*t*controlPts[2].x + t*t*t*controlPts[3].x
            if (x >= controlPts[1].x):
                break
            y = (1-t)*(1-t)*(1-t)*controlPts[0].y + 3*(1-t)*(1-t)*t*controlPts[1].y + 3*(1-t)*t*t*controlPts[2].y + t*t*t*controlPts[3].y
            results.append(point(x,y))

class hermite_spline(parametric_curve):
    def __init__(self, paramdict):
        super(hermite_spline, self).__init__(paramdict)
        self.nintervals = len(self.controlPoints) - 1
        
    def evalInterval(self, iintrvl, numpoints, results):
        controlPts = self.controlPoints[iintrvl:iintrvl + 2]
        primex1 = 0 if iintrvl == 0 else controlPts[0].x - self.controlPoints[iintrvl-1].x
        primey1 = 0 if iintrvl == 0 else controlPts[0].y - self.controlPoints[iintrvl-1].y
        primex2 = 0 if iintrvl == self.nintervals - 1 else self.controlPoints[iintrvl+1].x - controlPts[1].x
        primey2 = 0 if iintrvl == self.nintervals - 1 else self.controlPoints[iintrvl+1].y - controlPts[1].y
        controlPts.append(point(primex1, primey1))
        controlPts.append(point(primex2, primey2))
        for i in range(0, numpoints+1):
            t = float(i)/(numpoints)
            x = (2*t*t*t - 3*t*t + 1)*controlPts[0].x + (-2*t*t*t+3*t*t)*controlPts[1].x + (t*t*t - 2*t*t + t)*controlPts[2].x + (t*t*t - t*t)*controlPts[3].x
            y = (2*t*t*t - 3*t*t + 1)*controlPts[0].y + (-2*t*t*t+3*t*t)*controlPts[1].y + (t*t*t - 2*t*t + t)*controlPts[2].y + (t*t*t - t*t)*controlPts[3].y            
            results.append(point(x,y))

class b_spline(parametric_curve):
    
    x_func = ""
    y_func = ""
    
    def __init__(self, paramdict):
        #TODO: check for correct # of control pts
        super(b_spline, self).__init__(paramdict)
        self.nintervals = len(self.controlPoints) - 1
    
    def generateEqnSubexpression(self, iintrvl, xshift):
        #1. First get the correct list of control points, 
        #   we need to do a little of black magic and introduce reduntant control
        #   points to be able to interpolate between last/first control points and neighbours
        cp = self.getControlPointsForThisInterval(iintrvl)

        t3_term_x = -1*cp[0].x + 3*cp[1].x - 3*cp[2].x + cp[3].x
        t3_term_y = -1*cp[0].y + 3*cp[1].y - 3*cp[2].y + cp[3].y
        t2_term_x =  3*cp[0].x - 6*cp[1].x + 3*cp[2].x
        t2_term_y =  3*cp[0].y - 6*cp[1].y + 3*cp[2].y
        t1_term_x = -3 * cp[0].x + 3 * cp[2].x
        t1_term_y = -3 * cp[0].y + 3 * cp[2].y
        const_term_x = cp[0].x + 4*cp[1].x + cp[2].x
        const_term_y = cp[0].y + 4*cp[1].y + cp[2].y
        
        x_eqn = "if (ti == %d) { return (1.0/6)*( \
                      (t*t*t)*(%f) \
                    +   (t*t)*(%f) \
                    +     (t)*(%f) \
                    +         (%f) \
                ) }" % (iintrvl, t3_term_x, t2_term_x, t1_term_x, const_term_x+xshift)

        y_eqn = "if (ti == %d) { return (1.0/6)*( \
                      (t*t*t)*(%f) \
                    +   (t*t)*(%f) \
                    +     (t)*(%f) \
                    +         (%f) \
                ) }" % (iintrvl, t3_term_y, t2_term_y, t1_term_y, const_term_y)
        return [x_eqn, y_eqn]
    
    
    def generateEquationList(self, xshift):
        self.t_count = self.nintervals
        x_func = "function (t, ti) { ";
        y_func = "function (t, ti) { ";
        for i in range(0, self.nintervals):
            fpair = self.generateEqnSubexpression(i, xshift)
            x_func = x_func + fpair[0]
            y_func = y_func + fpair[1]
        
        x_func = x_func + "}";
        y_func = y_func + "}";
        
        self.x_func = x_func
        self.y_func = y_func
        return
    
    def getControlPointsForThisInterval(self, iintrvl):
        cp = []
        if (iintrvl < 2):
            cp.append(self.controlPoints[0])
        if (iintrvl > 1):
            cp.append(self.controlPoints[iintrvl-1])
        cp = cp + self.controlPoints[iintrvl:iintrvl + 3];
        cp = cp[0:4]
        while len(cp) < 4:
            cp.append(self.controlPoints[-1])
        return cp

    def evalInterval(self, iintrvl, numpoints, results):
        cp = self.getControlPointsForThisInterval(iintrvl)
        
        t3_term_x = -1*cp[0].x + 3*cp[1].x - 3*cp[2].x + cp[3].x
        t3_term_y = -1*cp[0].y + 3*cp[1].y - 3*cp[2].y + cp[3].y
        t2_term_x =  3*cp[0].x - 6*cp[1].x + 3*cp[2].x
        t2_term_y =  3*cp[0].y - 6*cp[1].y + 3*cp[2].y
        t1_term_x = -3 * cp[0].x + 3 * cp[2].x
        t1_term_y = -3 * cp[0].y + 3 * cp[2].y
        const_term_x = cp[0].x + 4*cp[1].x + cp[2].x
        const_term_y = cp[0].y + 4*cp[1].y + cp[2].y
        for i in range(0, numpoints+1):
            t = float(i)/(numpoints)
            x = float(1)/6 * (t*t*t*t3_term_x + t*t*t2_term_x + t*t1_term_x + const_term_x)
            y = float(1)/6 * (t*t*t*t3_term_y + t*t*t2_term_y + t*t1_term_y + const_term_y)
            results.append(point(x,y))
