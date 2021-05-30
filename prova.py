import osmnx
import pickle
import urllib
import csv
import networkx
import collections
from haversine import haversine
from staticmap import StaticMap, Line

PLACE = 'Barcelona, Catalonia'
GRAPH_FILENAME = 'barcelona.graph'
SIZE = 800
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'

Highway = collections.namedtuple('Highway', 'highway_id description coordinates')
Congestion = collections.namedtuple('Congestion', 'highway_id congestion')

def exist_graph(GRAPH_FILENAME):
    try:
        open(GRAPH_FILENAME)
        return True
    except:
        return False

def download_graph(PLACE):
    graph = osmnx.graph_from_place(PLACE, network_type='drive', simplify=True)
    return graph

def save_graph(graph, GRAPH_FILENAME):
    with open(GRAPH_FILENAME, 'wb') as file:
        pickle.dump(graph, file)

def load_graph(GRAPH_FILENAME):
    with open(GRAPH_FILENAME, 'rb') as file:
        graph = pickle.load(file)
    return graph

def download_digraph(graph):
    digraph = osmnx.utils_graph.get_digraph(graph, weight='length')
    return digraph

def to_pairs(coordinates):
    coords = coordinates.split(',')
    pairs = []
    i = 0
    while i < len(coords):
        pairs.append((float(coords[i]), float(coords[i + 1])))
        i += 2
    return pairs
    
def download_highways_congestions(HIGHWAYS_URL, CONGESTIONS_URL):
    highways_congestions = {}
    with urllib.request.urlopen(HIGHWAYS_URL) as response:
        lines = [l.decode('utf-8') for l in response.readlines()]
        reader = csv.reader(lines, delimiter=',')
        next(reader)  # ignore first line with description
        for line in reader:
            highway_id, description, coordinates = line
            highways_congestions.update({highway_id: [description, to_pairs(coordinates)]})
    with urllib.request.urlopen(CONGESTIONS_URL) as response:
        lines = [l.decode('utf-8') for l in response.readlines()]
        reader = csv.reader(lines, delimiter='#')
        for line in reader:
            congestion_id, date, actual_congestion, future_congestion = line
            highways_congestions.get(congestion_id).append(actual_congestion)
        return highways_congestions
    
def comparator(highway):
    return highway.highway_id

def download_highways(HIGHWAYS_URL):
    highways = []
    with urllib.request.urlopen(HIGHWAYS_URL) as response:
        lines = [l.decode('utf-8') for l in response.readlines()]
        reader = csv.reader(lines, delimiter=',')
        next(reader)
        for line in reader:
            highway_id, description, coordinates = line
            new_highway = Highway(highway_id = int(highway_id), description = description, coordinates = to_pairs(coordinates))
            highways.append(new_highway)
        highways.sort(key=comparator)
        print(len(highways), highways[len(highways) - 1].highway_id)
        return highways

def download_congestions(CONGESTIONS_URL):
    congestions = []
    with urllib.request.urlopen(CONGESTIONS_URL) as response:
        lines = [l.decode('utf-8') for l in response.readlines()]
        reader = csv.reader(lines, delimiter='#')
        for line in reader:
            congestion_id, date, actual_congestion, future_congestion = line
            congestion = Congestion(highway_id = int(congestion_id), congestion = int(actual_congestion))
            congestions.append(congestion)
        congestions.sort(key=comparator)
        print(len(congestions), congestions[len(congestions) - 1].highway_id)
        return congestions

def plot_highways(highways, file, SIZE):
    bcn_map = StaticMap(SIZE, SIZE)
    for highway in highways:
        line = Line(highway.coordinates, 'rgb(153,51,255)', 2)
        bcn_map.add_line(line)
    image = bcn_map.render()
    image.save(file)
    
def choose_color(n):   
    colors = ['rgb(128,128,128)', 'blue', 'green', 'rgb(255,255,0)', 'rgb(255,128,0)', 'red', 'rgb(0,0,0)']
    return colors[n]

def plot_congestions(congestions, highways, file, SIZE):
    bcn_map = StaticMap(SIZE, SIZE)
    for i in range(len(highways)):
        line = Line(highways[i].coordinates, choose_color(congestions[i].congestion), 2)
        bcn_map.add_line(line)
    image = bcn_map.render()
    image.save(file)
    
def create_itime(graph):
    for node1, info1 in graph.nodes.items():
        for node2, edge in graph.adj[node1].items():
            edge[0]["itime"] = 1000000000

def itime(length, congestion, maxspeed):
    if congestion == 6:
        return 1000000000
    return(length * 5 / (maxspeed * (6 - congestion)))

def nearest_node(graph, coord):
    nearest_node = None
    nearest_dist = 99999
    
    for node, info in graph.nodes.items():
        d = haversine((info['y'], info['x']), coord)
        if d < nearest_dist:
            nearest_dist = d
            nearest_node = node
    return nearest_node

def get_maxspeed(graph, start_node, finish_node):
    try:
        maxspeed = graph[start_node][finish_node]['maxspeed']
    except:
        return 50
    if type(maxspeed) == list:
        return int(max(maxspeed))
    else:
        return int(maxspeed)
    
def get_length(graph, start_node, finish_node):
    try:
        return float(graph[start_node][finish_node]['length'])
    except:
        return 30

def build_igraph(graph, highways, congestions):
    for i in range(len(highways) - 1):
        start_coord = highways[i].coordinates[0]
        finish_coord = highways[i].coordinates[len(highways[i].coordinates) - 1]
        start_node = nearest_node(graph, start_coord)
        finish_node = nearest_node(graph, finish_coord)
        list_nodes = osmnx.distance.shortest_path(graph, start_node, finish_node, weight='length')
        way_id = highways[i].highway_id
        congestion = congestions[i].congestion
        for j in range(len(list_nodes) - 1):
            length = get_length(graph, list_nodes[j], list_nodes[j + 1])
            maxspeed = get_maxspeed(graph, list_nodes[j], list_nodes[j + 1])
            graph[list_nodes[j]][list_nodes[j + 1]]['itime'] = itime(length, congestion, maxspeed)
    return graph

def main():
    # load/download graph (using cache)
    if exist_graph(GRAPH_FILENAME):
        graph = load_graph(GRAPH_FILENAME)
    else:
        graph = download_graph(PLACE)
        save_graph(graph, GRAPH_FILENAME)

    #osmnx.plot_graph(graph)
    
    #a = osmnx.basic_stats(graph)
    #print(a)

    congestions = download_congestions(CONGESTIONS_URL)
    highways = download_highways(HIGHWAYS_URL)
    #highways_and_congestions = download_highways_congestions(HIGHWAYS_URL, CONGESTIONS_URL)
    plot_highways(highways, 'highways.png', SIZE)
    plot_congestions(congestions, highways, 'congestions.png', SIZE)
    
    igraph = build_igraph(graph, highways, congestions)
    
main()