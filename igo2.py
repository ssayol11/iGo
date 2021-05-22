import collections
import osmnx
import pickle
import urllib
import csv
import networkx

PLACE = 'Barcelona, Catalonia'
GRAPH_FILENAME = 'barcelona.graph'
SIZE = 800
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'

#Highway = collections.namedtuple('Highway', '...') # Tram
#Congestion = collections.namedtuple('Congestion', '...')

def download_graph (PLACE):
    graph = osmnx.graph_from_place(PLACE, network_type='drive', simplify=True)
    graph = osmnx.utils_graph.get_digraph(graph, weight='length')
    return graph

def save_graph (graph, GRAPH_FILENAME):
    with open(GRAPH_FILENAME, 'wb') as file:
        pickle.dump(graph, file)

def load_graph (GRAPH_FILENAME):
    with open(GRAPH_FILENAME, 'rb') as file:
        graph = pickle.load(file)
    return graph

def main():
    # load/download graph (using cache)
    try:
        graph = load_graph(GRAPH_FILENAME)
    except:
        graph = download_graph(PLACE)
        save_graph (graph, GRAPH_FILENAME)

    osmnx.plot_graph(graph)

    highways = download_highways(HIGHWAYS_URL)
    plot_highways(highways, 'highways.png', SIZE)

main()
