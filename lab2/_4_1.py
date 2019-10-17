import numpy as np
import re
from sklearn.metrics import pairwise_distances_argmin_min, pairwise_distances

def loadAnimalData():
    with open("data/animalnames.txt") as f:
        names = np.array([ re.match("'(.*)'", name).group(1) for name in f.readlines() ])
    with open("data/animalattributes.txt") as f:
        attr = np.array([ attr[:-1] for attr in f.readlines() ])
    with open("data/animals.dat") as f:
        datapoints = np.array([int(a) for a in f.read().split(",")]).reshape(len(names),len(attr))
    
    return names, attr, datapoints

class SOM:

    def __init__(self, num_nodes, get_neighbors_func):
        self.num_nodes = num_nodes
        self.get_neighbors = get_neighbors_func

    def train(self, dataMatrix: np.ndarray, n_epochs=20, eta=0.2):
        
        num_features = dataMatrix.shape[1]

        nodes = np.random.uniform(low=0,high=1,size=(self.num_nodes, num_features))

        for ep in range(1,n_epochs+1):
            
            nb_size = (n_epochs - ep) + 5

            for p in dataMatrix:
                p = p.reshape(1,-1)

                center_arg, _ = pairwise_distances_argmin_min(p, nodes)
                nbs_args = self.get_neighbors(center_arg, nb_size)

                nodes[nbs_args] += eta * (p - nodes[nbs_args])

        self.nodes = nodes

    def showMap(self, dataMatrix, labels):

        label_arg = [ (label, pairwise_distances_argmin_min(p.reshape(1,-1), self.nodes)[0][0]) for label, p in zip(labels, dataMatrix) ]
        label_arg = sorted(label_arg, key=lambda x:x[1])
        print (label_arg)

if __name__ == "__main__":
    
    names, attr, datapoints = loadAnimalData()

    num_nodes = 100

    def get_neighbors_linear(center, nb_size):
        low = max(center - nb_size,0)
        high = min(center + nb_size, num_nodes-1)
        return np.arange(low, high+1)

    som = SOM(num_nodes, get_neighbors_linear)

    som.train(datapoints)
    som.showMap(datapoints, names)