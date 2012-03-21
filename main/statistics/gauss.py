# # # # # # # # # # # # # # # # # # #
# @author Alexander Novikov
#
#
# Main method implemented here is ge_solve:
#   solves a system of eq'ns matrix M x vec X = vec Y
#
#   NOTE: M,Y should contain only float elements!
#

POSITIVE_ZERO = +0.000000000000001
NEGEATIV_ZERO = -0.000000000000001


def iteration(M, Y, colRange, rowIndexesInit):
    rowIndexesLeft = [] + rowIndexesInit
    rowOrder = []
    
    # Forward-elimination
    for k in colRange:
        ci = -1
        for i in rowIndexesLeft:
            if M[i][k] > POSITIVE_ZERO or M[i][k] < NEGEATIV_ZERO:
                ci = i
                break
        
        if (ci  == -1):
            raise TypeError("Matrix not of full rank!")
        rowOrder.append(ci)
        rowIndexesLeft.remove(ci)
        
        divisor = M[ci][k]
        M[ci][k] = 1.0
        for j in range(k+1, len(M)):
            M[ci][j] = M[ci][j] / divisor
            
        Y[ci] = Y[ci] / divisor
        for r in rowIndexesLeft:
            if M[r][k] > POSITIVE_ZERO or M[r][k] < NEGEATIV_ZERO:
                factor = M[r][k]
                M[r][k] = 0.0
                for j in range(k+1, len(M)):
                    M[r][j] = M[r][j] - factor*M[ci][j]
                Y[r] = Y[r] - factor * Y[ci]
            else:
                M[r][k] = 0.0
    return rowOrder

# Return vector X of solutions to a
#   system of equations MX = Y
#
#   ASSUME M is a square matrix
#
def ge_solve(M, Yorig):
    Y = [] + Yorig
    #1. Pick a row to start, any row with non-zero M[j][0] will do
    colIndex = 0
    
    #2. Now perform GE with pivoting
    #
    # k - current column
    rowOrder = iteration(M,Y,range(0, len(M)), range(0, len(M)))
    # Back-elimination
    brange = range(0, len(M))
    brange.reverse()
    rowOrder.reverse()
    
    iteration(M, Y, brange, rowOrder)
    return Y
    
    

#M = [
#    [0.0, 2.0, 0.0],
#    [2.0, 0.0, 0.0],
#    [0.0, 0.0, 3.0],
#]
#Y = [1.0, 2.0, 3.0]    
#
#X = ge_solve(M, Y)

#M = [
#    [ 2.0, 0.0, 1.0],
#    [ 0.0, 2.0, 0.5],
#    [ 2.0, 0.0, 1.0]
#]
#Y = [9.0, 10.0, 11.0]
#X = ge_solve(M, Y)
#M = [
#    [1.0, 2.0, 3.0],
#    [1.0, 3.0, 5.0],
#    [1.0, 7.0, 9.0],
#]
#Y = [1.0, 2.0, 3.0]

#X = ge_solve(M, Y)

#print X

    