# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# @author Alexander Novikov
#
# Here are implementations of several stages of multi-stage clustering
# before we can use B-splines for regression
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
import math

from main.statistics.geom2d import cluster

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# This is a nifty agorithm which does a pretty good job at clustering regression points together
# The downside, is, that is even MORE computationally expensive than k-means clustering ]:D
#
#   Params: thresh  : 0<thresh <1, threshold of confidence of cluster merge wrt competition with other clusters
#           thresh2 : 0<thresh2<1, to allow merge with clusters of centroids within thresh2*stddev to this centroid
#
#
def do_cluster1(points, thresh = 0.3333, thresh2 = 1, rate=0.5):
    #0. Initialize every point to be a cluster
    clusters = []
    for point in points:
        cls = cluster()
        cls.addPoint(point)
        clusters.append(cls)
    
    #1. Do iterative cluster merge until convergence
    change =  True
    while change:
        # compute inter-cluster differences
        change = False
        distances={}
        for i in range(0, len(clusters)):
            distances[i] = {}
        
        for i in range(0, len(clusters)):
            distances[i][i] = (1 << 31)
            for j in range(i+1, len(clusters)):
                dist = clusters[i].distanceTo(clusters[j])
                distances[i][j] = dist
                distances[j][i] = dist
        
        merge_clusters = []
        remove_clusters = []
        picked_indices = set()
        # check whether we can merge 2 clusters 
        for i in range(0, len(clusters)):
            if i in picked_indices:
                continue
            # find max index in i-th row
            minJForI = 0
            minJForIVal = float(1 << 31)
            for j in range(0, len(clusters)):
                if (minJForIVal > distances[i][j]):
                    minJForI = j
                    minJForIVal = distances[i][j]
            #print "for i = %d desc = %s, min cluster is j = %d, desc= %s" % (i, clusters[i], minJForI, clusters[minJForI])  
            # find max index in minJForI-th row
            minJForJ = 0
            minJForJ2ndBest = 0
            minJForJVal = float(1 << 31)
            minJForJVal2ndBest = float(1 << 31)
            for j in range(1, len(clusters)):
                if (minJForJVal > distances[minJForI][j]):
                    minJForJ2ndBest = minJForJ
                    minJForJ = j 
                    minJForJVal2ndBest = minJForJVal
                    minJForJVal = distances[minJForI][j] 
            # this means these 2 clusters are each other's nearest neighbours
            # and are below threshold relative to other cluster's 2nd nearest neighbour
            if minJForJ == i:
                #if minJForIVal <= thresh * minJForJVal2ndBest:
                #print "[DEBUG] %s : %s" % (str(clusters[i].centroid()), str(clusters[i]))
                mergeCompetitive = (minJForIVal <= thresh * minJForJVal2ndBest)
                mergeGaussianCond = (len(clusters[i].points) == 1) or (minJForIVal <= thresh2 * clusters[i].stddev_xy())
                if mergeCompetitive and mergeGaussianCond:
                    #print "MERGING [%f] %s, INFO: %f %s | %f %s" % (clusters[i].stddev_xy(), str(clusters[i]), minJForIVal, str(clusters[minJForI]), minJForJVal2ndBest, str(clusters[minJForJ2ndBest]))
                    merge_clusters.append([i, minJForI])
                    remove_clusters.append(minJForI)
                    picked_indices.add(i)
                    picked_indices.add(minJForI)
                else:
                    #print "ABORTING MERGE %s, thresh NOT GOOD: %f %s | %f %s" % (str(clusters[i]), minJForIVal, str(clusters[minJForI]), minJForJVal2ndBest, str(clusters[minJForJ2ndBest]))
                    pass
        
        # do the merge of picked clusters:
        for cluster_pair in merge_clusters:
            change = True
            i = cluster_pair[0]
            j = cluster_pair[1]
            for point in clusters[j].points:
                clusters[i].addPoint(point)
        
        clustersNew = []
        for i in range(0, len(clusters)):
            if not i in remove_clusters:
                clustersNew.append(clusters[i])
        clusters = clustersNew
        
        thresh2 = thresh2 * rate
    return clusters



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This algorithm shuffles around points to/from clusters
#   with intersecting x-ranges.
#
#
def do_cluster2(clusters):
    xMaxes = {}
    xMins = {}
    for ci in range(0, len(clusters)):
        xMaxes[ci] = -(1 << 31)
        xMins [ci] =  (1 << 31)
        for point in clusters[ci].points:
            xMaxes[ci] = xMaxes[ci] if xMaxes[ci] > point.x else point.x
            xMins [ci] = xMins [ci] if xMins [ci] < point.x else point.x
    
    # search for intersections:
    changing = True
    while changing:
        changing = False
        newClusters = []
        removeClusters = []
        for i in range(0, len(clusters)):
            for j in range(i+1, len(clusters)):
                if (xMins[j] >= xMins[i] and xMins[j] <= xMaxes[i]):
                    # xrange collision detected
                    if True and (xMaxes[j] <= xMaxes[i]):
                        # The cluster is subsumed by this one, need to split ranges
                        clsPartBeforeInt = cluster()
                        clsPartInt = clusters[j]
                        clsPartAfterInt = cluster()
                        xMaxes[i] = -(1 << 31)
                        xMins [i] =  (1 << 31)
                        newMax    = -(1 << 31)
                        newMin    =  (1 << 31)
                        #ptc = len(clusters[i].points) + len(clusters[j].points)
                        for point in clusters[i].points:
                            if point.x < xMins[j]:
                                xMaxes[i] = xMaxes[i] if xMaxes[i] > point.x else point.x
                                xMins [i] = xMins [i] if xMins [i] < point.x else point.x
                                clsPartBeforeInt.addPoint(point)
                            elif point.x > xMaxes[j]:
                                clsPartAfterInt.addPoint(point)
                                newMax = newMax if newMax > point.x else point.x
                                newMin = newMin if newMin < point.x else point.x
                            else:
                                clsPartInt.addPoint(point)
                        #ptf = len(clsPartBeforeInt.points) + len(clsPartInt.points) + len(clsPartAfterInt.points)
                        #if (ptf != ptc):
                            #print "ERROR! POINTS LOST"
                        # replace 2 intersecting clusters with disjoint clusters,
                        # add a new cluster
                        clusters[i] = clsPartBeforeInt
                        clusters[j] = clsPartInt
                        if len(clusters[i].points) == 0:
                            removeClusters.append(i)
                        if len(clusters[j].points) == 0:
                            #print "LEAVING INT EMPTY"
                            removeClusters.append(j)
                        if len(clsPartAfterInt.points) != 0:
                            newClusters.append([clsPartAfterInt, newMax, newMin])
                        
                    if True and (xMaxes[j] > xMaxes[i]):
                        # There is an intersection which is a proper subset
                        # Create a new intersection cluster
                        clsPartBeforeInt = cluster()
                        clsPartInt = cluster()
                        clsPartAfterInt = cluster()
                        # perform a 3-way partition
                        xMaxes[i] = -(1 << 31)
                        xMins [i] =  (1 << 31)
                        xMaxes[j] = -(1 << 31)
                        xMins [j] =  (1 << 31)
                        newMax    = -(1 << 31)
                        newMin    =  (1 << 31)
                        for point in clusters[i].points:
                            if point.x < xMins[j]:
                                xMaxes[i] = xMaxes[i] if xMaxes[i] > point.x else point.x
                                xMins [i] = xMins [i] if xMins [i] < point.x else point.x
                                clsPartBeforeInt.addPoint(point)
                            else:
                                clsPartInt.addPoint(point)
                                newMax = newMax if newMax > point.x else point.x
                                newMin = newMin if newMin < point.x else point.x
                        for point in clusters[j].points:
                            if point.x < xMaxes[i]:
                                clsPartInt.addPoint(point)
                                newMax = newMax if newMax > point.x else point.x
                                newMin = newMin if newMin < point.x else point.x
                            else:
                                xMaxes[j] = xMaxes[j] if xMaxes[j] > point.x else point.x
                                xMins [j] = xMins [j] if xMins [j] < point.x else point.x
                                clsPartAfterInt.addPoint(point)
                        # replace 2 intersecting clusters with disjoint clusters,
                        # add a new cluster
                        clusters[i] = clsPartBeforeInt
                        clusters[j] = clsPartAfterInt
                        
                        if len(clusters[i].points) == 0:
                            #print "[1] LEAVING BEFORE EMPTY"
                            removeClusters.append(i)
                        if len(clusters[j].points) == 0:
                            #print "[2] LEAVING AFT EMPTY"
                            removeClusters.append(j)
                        if len(clsPartInt.points) != 0:
                            newClusters.append([clsPartInt, newMax, newMin])

        #end for i in range
        #remove empty clusters
        #print ""
        #print ""
        #print "=============="
        clustersPrime = []
        xMaxesPrime = {}
        xMinsPrime = {}
        for ci in range(0,len(clusters)):
            if not ci in removeClusters:
                clustersPrime.append(clusters[ci])
                #xMaxesPrime.append(xMaxes[ci])
                #xMinsPrime.append(xMins[ci])
                xMaxesPrime[len(xMaxesPrime)] = xMaxes[ci]
                xMinsPrime[len(xMinsPrime)] = xMins[ci]
                #print "%s" % (clusters[ci])
        clusters = clustersPrime
        xMaxes = xMaxesPrime
        xMins = xMinsPrime
        for newclus in newClusters:
            #print "%s" % (newclus[0])
            changing = True
            newindex = len(clusters)
            clusters.append(newclus[0])
            xMaxes[newindex] = newclus[1]
            xMins [newindex] = newclus[2]
    #end while chaging
    sortedIndices = sorted(range(0, len(clusters)), lambda i, j: cmp(xMins[i],xMins[j]))
    sortedClusters = map( lambda ci: clusters[ci], sortedIndices)
    sortedXMaxes = map( lambda ci: xMaxes[ci], sortedIndices)
    sortedXMins = map( lambda ci: xMins[ci], sortedIndices)
    result = {}
    result['clusters'] = sortedClusters
    result['xmaxes']    = sortedXMaxes
    result['xmins' ]    = sortedXMins
    return result


# # # # # # # # # # # # # # # # # # # # # # # # # # # 
# Using the hermite spline formula we can
# infer by derivative when constraint is violated,
# return True in that case
def nondecreasing_x_hermite_check(p0, m0, p1, m1):
    POSITIVE_ZERO = +0.000000001
    NEGATIVE_ZERO = -0.000000001
    #0. Compute t^2, t, and constant terms
    k0 = 6*p0.x - 6*p1.x + 3*m0.x - 3*m1.x
    k1 = -6*p0.x - 4*m0.x + 6*p1.x - 2*m1.x
    k2 = m0.x
    
    # Solve quadratic equaltion here:    
    d = k1 * k1 - 4 * k0 * k2 # d = b^2 - 4ac
    if d < POSITIVE_ZERO:
        # This is safe then, x will not have extremum at this interval
        return False
    t1 = -k1 + math.sqrt(d) / (2*k0)
    t2 = -k1 + math.sqrt(d) / (2*k0)
    condition = not ((t1 < NEGATIVE_ZERO) or (t1 > 1 + POSITIVE_ZERO)) and ((t2 < NEGATIVE_ZERO) or (t2 > 1 + POSITIVE_ZERO))
    return condition
    
# # # # # # # # # # # # # # # # # # # # # # # # # # #
# This algorithm uses hermite spline equation properties to
# merge certain clusters together if they offend    #
# nondecreasing x property of the parametric curve  #
# # # # # # # # # # # # # # # # # # # # # # # # # # #
# Assume all parameters sorted in cluster ascending order
def do_cluster3(paramdict, constraintViolationFunc=nondecreasing_x_hermite_check):
    clusters = paramdict['clusters']
    xMins    = paramdict['xmins']
    xMaxes   = paramdict['xmaxes']
    
    changing = True
    while changing:
        changing = False
        removeClusters = []
        # Only two successor clusters can offend this property
        for i in range(1, len(clusters)):
            p0 = clusters[i-1].centroid()
            p1 = clusters[ i ].centroid()
            m0 = point(0,0) if i == 1 else point(clusters[i-1].centroid().x - clusters[i-2].centroid().x, clusters[i-1].centroid().y - clusters[i-2].centroid().y)
            m1 = point(0,0) if i == len(clusters)-1 else point(clusters[i+1].centroid().x - clusters[i].centroid().x, clusters[i+1].centroid().y - clusters[i].centroid().y)
            if constraintViolationFunc(p0, m0, p1, m1):
                for pt in clusters[i-1].points:
                    clusters[i].addPoint(pt)
                removeClusters.append(i-1)
                # TODO: merge clusters to the new index i, add i-1 to remove indices
        changing = 0 != len(removeClusters)
        if changing:
            acceptIndices = filter(lambda ci: not ci in removeClusters, range(0, len(clusters)))
            clusters = map(lambda cx: clusters[cx],  acceptIndices)
            xMins    = map(lambda cx: xMins[cx], acceptIndices)
            xMaxes   = map(lambda cx: xMaxes[cx], acceptIndices)
        pass
    paramdict['clusters'] = clusters
    paramdict['xmins'] = xMins
    paramdict['xmaxes'] = xMaxes
    return paramdict
