"""The SOINN regressor."""
import isoinn2
from kde import density
from __gaussian_custom import norm_pdf_multivariate
from numpy import array,diag,matrix
import time
from pygraph.classes.graph import graph
from pygraph.algorithms.accessibility import connected_components
import itertools
from copy import deepcopy
from gks import GKS

class ISOINNregressor:
    """Regression interface based on SSL-GKS and SOINN.
    smooth can be set to None or real number, normally falls in [-1,0]. If set to None, SSL will be employed to estimate its value.
    response_dimension is integer, means the number of response variables.
    K is integer which is the number of neurons for kernel smoothing, larger K means little details but more smoothed predictions.
    The rest of the parameters are GNG training parameters."""
    Pis = [] #:Distribution of the neuron populations.
    bands = [] #:Bandwidth for visualization.
    nodes = [] #:Weights of the neurons.
    sigmax = 0
    ux = []
    uy = []
    gr = 0 #:Topology structure of neurons.
    counts = 0
    standard_deviation = 0
    smooth = -0.4 #:Smooth parameter for kernel smoothing, if set to None, SSL smooth parameter selection will be employed.
    reg_model = None
    __res_dimension = 1
    __global = False
    __inn_parameter_list = []
    K = 10 #:Number of neurons selected for kernel smoothing.
    
    def __init__(self, smooth = None, response_dimension = 1, K = 10, age_max = 200, nn_lambda = 60, alpha = 10,del_noise = True):
        isoinn2.set_parameter(age_max,nn_lambda,alpha,0,del_noise)
        self.__inn_parameter_list = [age_max,nn_lambda,alpha,0,del_noise]
        self.smooth = smooth
        self.__res_dimension = 1
        self.K = K

    def fit(self, X, y):
        """X is array or list, each element is numpy array. Y is array or list containing the response varaible values."""
        print 'training with bandwidth calculation, please wait...'
        timecost = time.time()
        t = 0
        for i in range(len(y)):
            n_point = array(list(X[i]) + list([y[i]]))
            if t == 0:
                EX = n_point
                EX2 = n_point ** 2
            else:
                count = float(t)
                EX = (EX*count/(count + 1.0)) + (n_point/(count + 1.0))
                EX2 = (EX2*count/(count + 1.0)) + ((n_point ** 2)/(count + 1.0))
            t += 1
            isoinn2.step(n_point,0,t)
        isoinn2.step(array([]),0,-1)
        print 'time cost',time.time() - timecost
        standard_deviation = (EX2 - EX ** 2) ** 0.5
        self.standard_deviation = standard_deviation
        if self.smooth == None:
            self.bands = standard_deviation * (len(isoinn2.setN) ** (-0.2))
        else:
            self.bands = standard_deviation * (len(isoinn2.setN) ** (self.smooth))
        Pis = isoinn2.accumulated
        self.counts = isoinn2.accumulated
        self.Pis = array(Pis) / float(sum(array(Pis)))#distribution of the clusters
        self.nodes = deepcopy(isoinn2.setN)
        self.sigmax = matrix(diag(array(self.bands)[0:-1]**2))
        for each in self.nodes:
            self.ux.append(each[0:-1])
            self.uy.append(each[-1])
        self.uy = array(self.uy)
        self.gr = isoinn2.gr
        self.reg_model = GKS(self.nodes, self.counts, standard_deviation**2, self.__res_dimension, self.smooth, self.K)
        
    def predict(self, data):
        """This method returns the predictions the variable data. data should be within the same data space to X in the fit method. When smooth parameter is set to None, an SSL
        procedure will be employed to estimate it."""
        if self.smooth == None:
            isoinn2.set_parameter(self.__inn_parameter_list[0],self.__inn_parameter_list[1],self.__inn_parameter_list[2],self.__inn_parameter_list[3],self.__inn_parameter_list[4])
            t = 0
            for i in range(len(data)):
                n_point = array(data[i])
                if t == 0:
                    EX = n_point
                    EX2 = n_point ** 2
                else:
                    count = float(t)
                    EX = (EX*count/(count + 1.0)) + (n_point/(count + 1.0))
                    EX2 = (EX2*count/(count + 1.0)) + ((n_point ** 2)/(count + 1.0))
                t += 1
                isoinn2.step(n_point,0,t)
            isoinn2.step(array([]),0,-1)
            return self.reg_model.responses(data, isoinn2.setN)
        else:
            return self.reg_model.responses(data)

    def draw_density(self, resolution = 0.05):
        """Draws the density contour of any regressor instance. It can only be called after calling the fit
        method, and only work in 2d case. resolution is a postitive real number definining the detail level of drawing.
        A smaller resolution number will generate more detailed drawings."""
        from numpy import mgrid,zeros
        from copy import deepcopy
        the_d = density(self.nodes,array(self.counts),self.standard_deviation)
        dx, dy = resolution, resolution

        # generate 2 2d grids for the x & y bounds
        y, x = mgrid[slice(0, 1 + dy, dy),slice(0, 1 + dx, dx)]
        t=deepcopy(x[0])

        z = zeros(shape = (len(x[0]),len(y[0])))
        z1= zeros(shape = (len(x[0]),len(y[0])))
        print('Please wait...')
        for i in range(len(t)):
            for j in range(len(t)):
                input_point = array([t[i],t[j]])
                z[j][i] = the_d.estimate(input_point)
                if not ((input_point - array([0.5,0.2])).any()):
                    print i,j
        print('drawing...')

        import matplotlib.pyplot as plt
        from matplotlib.colors import BoundaryNorm
        from matplotlib.ticker import MaxNLocator
        z = z[:-1, :-1]
        levels = MaxNLocator(nbins=15).bin_boundaries(z.min(), z.max())
        cmap = plt.get_cmap('PiYG')

        plt.contourf(x[:-1, :-1] + dx / 2., y[:-1, :-1] + dy / 2., z, levels=levels, cmap=cmap)
        plt.colorbar()
        plt.title('Density estimation by SOINN')
        plt.show()
        

if __name__ == '__main__':
    from utils import csv_reader
    r = csv_reader('reg_intro.csv')
    X,y = r.separate_label()
    the_reg = ISOINNregressor(smooth = -0.4, K = 15)
    the_reg.fit(X,y)
#    the_reg.draw_density()
    test_x = []
    draw_x = []
    for i in range(50):
        test_x.append(array([i/50.0]))
        draw_x.append(i/50.0)
    test_y = the_reg.predict(test_x)
    import matplotlib.pyplot as plt
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(draw_x,test_y,'k-')
    plt.axis('off')
    plt.show()
