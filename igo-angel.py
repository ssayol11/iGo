import collections
import osmnx
import pickle
import urllib
import csv
import networkx
from staticmap import StaticMap, Line
from haversine import haversine

PLACE = 'Barcelona, Catalonia'
GRAPH_FILENAME = 'barcelona.graph'
SIZE = 800
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'

def download_graph (PLACE):
    graph = osmnx.graph_from_place(PLACE, network_type='drive', simplify=False)
    graph = osmnx.add_edge_speeds(graph)
    #graph = osmnx.utils_graph.get_digraph(graph, weight='length')
    return graph

def save_graph (graph, GRAPH_FILENAME):
    with open(GRAPH_FILENAME, 'wb') as file:
        pickle.dump(graph, file)

def load_graph (GRAPH_FILENAME):
    with open(GRAPH_FILENAME, 'rb') as file:
        graph = pickle.load(file)
    return graph

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

def plot_highways(highways_congestions, file, SIZE):
    bcn_map = StaticMap(SIZE, SIZE)
    for key in highways_congestions:
        line = Line(highways_congestions.get(key)[1], 'rgb(153,51,255)', 2)
        bcn_map.add_line(line)
    image = bcn_map.render()
    image.save(file)

def choose_colour(n):
    colours = ['rgb(128,128,128)', 'blue', 'green', 'rgb(255,255,0)', 'rgb(255,128,0)', 'red', 'rgb(0,0,0)']
    return colours[n]

def plot_congestions(highways_congestions, file, SIZE):
    bcn_map = StaticMap(SIZE, SIZE)
    for key in highways_congestions:
        line = Line(highways_congestions.get(key)[1], choose_colour(int(highways_congestions.get(key)[2])), 4)
        bcn_map.add_line(line)
    image = bcn_map.render()
    image.save(file)

def itime(length, congestion, maxspeed):
    return(length * 5 / (maxspeed * (6 - congestion)))

def nearest_node(graph, coord):
    nearest_node = None
    nearest_dist = 99999
    
    for node, info in graph.nodes.items():
        d = haversine((info['x'], info['y']), coord)
        if d < nearest_dist:
            nearest_dist = d
            nearest_node = node
    return nearest_node

def build_igraph(graph, highways_congestions):
    for key in highways_congestions:
        if highways_congestions.get(key)[2] != 0 and highways_congestions.get(key)[2] != 6:
            start_coord = highways_congestions.get(key)[1][0]
            finish_coord = highways_congestions.get(key)[1][len(highways_congestions.get(key)[1]) - 1]
            start_node = nearest_node(graph, start_coord)
            finish_node = nearest_node(graph, finish_coord)
            print(start_node, finish_node)
            try:
                list_nodes = networkx.shortest_path(graph, start_node, finish_node)
                for j in range(len(list_nodes) - 1):
                    first_node = list_nodes[j]
                    second_node = list_nodes[j + 1]
                    length = float(graph.adj[first_node][second_node][0]["length"])
                    maxspeed = None
                    if (type(graph.adj[first_node][second_node][0]["maxspeed"] == list)):
                        maxspeed = float(graph.adj[first_node][second_node][0]["maxspeed"][0])
                    else:
                        maxspeed = float(graph.adj[first_node][second_node][0]["maxspeed"])
                        graph.adj[first_node][second_node][0]["itime"] = itime(length, highways_congestions.get(key)[2], maxspeed)
            except:
                pass

    return graph

def main():
    # load/download graph (using cache)
    try:
        graph = load_graph(GRAPH_FILENAME)
    except:
        graph = download_graph(PLACE)
        save_graph(graph, GRAPH_FILENAME)


    #print(graph.nodes[2108122003]['y'], graph.nodes[2108122003]['x'])
    #
    #print(graph.nodes[2108122003]['y'], graph.nodes[308672459]['x'])
    #print(graph.nodes[2108122003])
    #print(networkx.shortest_path(graph, 390227138, 687897113))
    #print(osmnx.nearest_edges(graph,41.3806406,2.1186115))
    #print(osmnx.nearest_nodes(graph, 2.101502862881051,41.3816307921222))
    #for edge in graph.adj[1425252270].items():
    #    print(edge)
    #print(graph.nodes[3509102852]['y'], graph.nodes[3509102852]['x'])
    highways_and_congestions = download_highways_congestions(HIGHWAYS_URL, CONGESTIONS_URL)
    plot_highways(highways_and_congestions, 'highways.png', SIZE)
    plot_congestions(highways_and_congestions, 'congestions.png', SIZE)

    igraph = build_igraph(graph, highways_and_congestions)
    
    #for node, info in graph.nodes.items():
     #   print(node, info)


main()