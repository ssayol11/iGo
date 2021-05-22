import collections
import osmnx
import pickle
import urllib
import csv
import networkx
from staticmap import StaticMap, Line

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

def to_pairs(coordinates):
    coords = coordinates.split(',', 4)
    return list([(float(coords[0]), float(coords[1])), (float(coords[2]), float(coords[3]))])

def download_highways(HIGHWAYS_URL):
    with urllib.request.urlopen(HIGHWAYS_URL) as response:
        lines = [l.decode('utf-8') for l in response.readlines()]
        reader = csv.reader(lines, delimiter=',', quotechar='"')
        next(reader)  # ignore first line with description
        highways = {}
        for line in reader:
            way_id, description, coordinates = line
            highways.update({way_id: [description, to_pairs(coordinates)]})
        return highways

def plot_highways(highways, file, SIZE):
    bcn_map = StaticMap(SIZE, SIZE) 
    for key in highways:
        line = Line(highways.get(key)[1], 'blue', 2)
        bcn_map.add_line(line)
    image = bcn_map.render()
    image.save(file)

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
