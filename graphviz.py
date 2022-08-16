from matplotlib import pyplot as plt
import networkx as nx

class GraphVisualization:
    def __init__(self):
        pass


if __name__ == '__main__':
    # First networkx library is imported 
    # along with matplotlib
    import networkx as nx
    import matplotlib.pyplot as plt
    
    
    # Defining a Class
    class GV:
        def __init__(self):
            self.visual = []

        def addEdge(self, a, b):
            temp = [a, b]
            self.visual.append(temp)
            
        def visualize(self):
            G = nx.Graph()
            G.add_edges_from(self.visual)
            nx.draw_networkx(G)
            plt.show()
    
    # Driver code
    G = GV()
    G.addEdge(0, 2)
    G.addEdge(1, 2)
    G.addEdge(1, 3)
    G.addEdge(5, 3)
    G.addEdge(3, 4)
    G.addEdge(1, 0)
    G.visualize()