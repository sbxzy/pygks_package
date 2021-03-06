"""The single layer SOINN algorithm procedures, for developers only."""
from numpy import *
from . import __grouping2 as grouping2
from math import isnan
from oldgraph.classes.graph import graph

winner_index = 0
winner_2nd_index = 0
setN = [] #:neuron weights
gr = graph() #:topology structure implemented by python-graph
T_winner = 0
T_2nd_winner = 0
accumulated = [1,1]
big_clusters = []
density = []
age_max = 0
nn_lambda = 0
alpha = 0
t = 1
numbers = [1,1]
setLabel = [0,0]
miminum_cluster = 2
delete_noise = False


def set_parameter(age,lambda_set,alpha_set,min_cluster,if_delete):
    """Initilization of SOINN, calling this function after training will reset the
    neural network for further training. age, lambda_set, alpha_set,min_cluster,if_delete
    are the SOINN parameters meaning max age, learning step, neuron clustering coefficient,
    minimum desired clusters and a choice whether to delete the neurons without neighbors
    in the final round of training."""
    global age_max
    global nn_lambda
    global alpha
    global setN
    global accumulated
    global numbers
    global density
    global big_clusters
    global t
    global minimum_cluster
    global gr
    global delete_noise
    delete_noise = if_delete
    t = 1
    setN = []
    accumulated = [1,1]
    numbers = [1,1]
    setLabel = [0,0]
    big_clusters = []
    density = []
    nn_lambda = lambda_set
    age_max = age
    alpha = alpha_set
    minimum_cluster = min_cluster
    gr = graph()
    return

def min_max_in_tresholds(neighbours,index):
    global setN
    treshold = 0.0
    if len(neighbours) == 0:
        distances = sum(pow(array(setN - setN[index]),2),axis = -1)**0.5
        distances[index] = float('inf')
        treshold = min(distances)
    else:
        distances = []
        i = 0
        for i in neighbours:
            distances.append(linalg.norm(setN[i] - setN[index]))
        treshold = max(distances)
    return treshold

def tresholds():
    global setN
    global T_winner
    global T_2nd_winner
    global gr
    winner_neighbours = gr.neighbors(winner_index)
    T_winner = min_max_in_tresholds(winner_neighbours,winner_index)

    winner_2nd_neighbours = gr.neighbors(winner_2nd_index)
    T_2nd_winner = min_max_in_tresholds(winner_2nd_neighbours,winner_2nd_index)
    return

def neighbour_count(index):
    global gr
    return len(gr.neighbors(index))

def remove_node(index):
    """Remove a neuron specified by 'index'."""
    global setN
    global numbers
    global gr
    bf = gr.neighbors(index)
    bfc = len(gr.neighbors(len(setN)-1))
    if (len(setN)-1) in bf:
        bfc -= 1
    distances = sum(pow(array(setN - setN[index]),2),axis = -1)
    distances[index] = float('inf')
    winner_index = argmin(distances)
    a = distances[winner_index]
    distances[winner_index] = float('inf')
    second_index = argmin(distances)
    b = distances[second_index]
    if (a+b) == 0.0:
        numbers[winner_index] += numbers[index]
    else:
        numbers[winner_index] += b/(a+b)*numbers[index]
        numbers[second_index] += a/(a+b)*numbers[index]

    last_node = len(setN) - 1
    #delete edges of the index
    index_neighbors = gr.neighbors(index)
    for each_node in index_neighbors:
        gr.del_edge((index,each_node))
    last_node_neighbors = gr.neighbors(last_node)
    for each_node in last_node_neighbors:
        gr.add_edge((each_node,index))
        gr.set_edge_weight((each_node,index),gr.get_edge_properties((each_node,last_node))['weight'])
    gr.del_node(last_node)
    setN[index] = setN[last_node]
    accumulated[index] = accumulated[last_node]
    numbers[index] = numbers[last_node] + numbers[index]
    setN.pop(-1)
    accumulated.pop(-1)
    numbers.pop(-1)
    if len(setN) != index:
        if len(gr.neighbors(index)) != bfc:
            print(index,bfc,gr.neighbors(index))
            input('remove error')
    return

def come_together():
    big_clusters = grouping2.group(setN,gr,False,minimum_cluster,alpha)
    return

def stop_and_write():
    global delete_noise
    i = 0
    if delete_noise:
        while (i != len(setN)) & (len(setN) > 2):
            
            if neighbour_count(i) <= 1:
                remove_node(i)
            else:
                i += 1
    big_clusters = grouping2.group(setN,gr,True,minimum_cluster,alpha)
    #print 'end training SOINN!'
    return


def step(point,pLabel,tx):
    """The SOINN training procedures in each step. 'point' is the
    input vector. 'pLabel' is the label of the input vector and
    set to 0 if unlabeled. 'tx' is the mark for end training
    (when set to -1)."""
    global winner_index
    global winner_2nd_index
    global setN
    global t

    if t == 1:
        setN.append(point)
        gr.add_node(0)

    elif t == 2:
        setN.append(point)
        gr.add_node(1)

    elif tx == -1:#-1 means training is over
        stop_and_write()
    else:
        distances = sum((array(setN - point))**2,axis = -1)
        winner_index = argmin(distances)
        distances[winner_index] = float('inf')
        winner_2nd_index = argmin(distances)
        tresholds()
        if ((linalg.norm(point - setN[winner_index]) > T_winner) | (linalg.norm(point - setN[winner_2nd_index]) > T_2nd_winner)):
            gr.add_node(len(setN))
            setN.append(point)
            accumulated.append(1)
            numbers.append(1)
        else:
            accumulated[winner_index] += 1
            numbers[winner_index] += 1
            if gr.has_edge((winner_index,winner_2nd_index)) == False:
                gr.add_edge((winner_index,winner_2nd_index))
                gr.set_edge_weight((winner_index,winner_2nd_index),0)
            setN[winner_index] += 1/float(accumulated[winner_index])*(point - setN[winner_index])
            i = 0
            for i in range(len(setN)):
                if gr.has_edge((winner_index,i)):
                    setN[i] += 1/(100.0*accumulated[winner_index])*(point - setN[i])
                    gr.set_edge_weight((winner_index,i),(gr.get_edge_properties((winner_index,i))['weight']+1))
                    if gr.get_edge_properties((winner_index,i))['weight'] > age_max:
                        gr.del_edge((winner_index,i))
        if (t + 1) % nn_lambda == 1:
            neighbor_counts = []
            for i in range(len(setN)):
                neighbor_counts.append(neighbour_count(i))
            i = 0
            while (i != len(setN)) & (len(setN) > 2):
                if neighbor_counts[i] <= 1:
                   remove_node(i)
                   neighbor_counts[i] = neighbor_counts[-1]
                   neighbor_counts.pop(-1)
                else:
                    i += 1
            come_together()
    t += 1
        
