import osmnx
import pickle
import urllib
import csv
import osmnx
from haversine import haversine
from staticmap import StaticMap, Line

PLACE = 'Barcelona, Catalonia'
GRAPH_FILENAME = 'barcelona.graph'
SIZE = 800
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'


def exist_graph(GRAPH_FILENAME):
    # Returns true if the graph named "GRAPH_FILENAME" is already downloaded or false otherwise.
    try:
        open(GRAPH_FILENAME)
        return True
    except:
        return False


def download_graph(PLACE):
    # Download the simplified graph of the "PLACE" location using the osmnx library.
    graph = osmnx.graph_from_place(PLACE, network_type='drive', simplify=True)
    return graph


def save_graph(graph, GRAPH_FILENAME):
    # Save the graph "graph" to a file named "GRAPH_FILENAME".
    with open(GRAPH_FILENAME, 'wb') as file:
        pickle.dump(graph, file)


def load_graph(GRAPH_FILENAME):
    # Load the graph "GRAPH_FILENAME" if it has been previously downloaded and saved.
    with open(GRAPH_FILENAME, 'rb') as file:
        graph = pickle.load(file)
    return graph


def download_digraph(graph):
    # Converts the MultiDiGraph "graph" to a DiGraph using the "lenght" parameter to choose between parallel edges.
    digraph = osmnx.get_digraph(graph, weight='length')
    return digraph


def to_pairs(coordinates):
    # Group in pairs the elements of a vector that contains an even number of decimal numbers.
    coords = coordinates.split(',')
    pairs = []
    i = 0
    while i < len(coords):
        pairs.append((float(coords[i]), float(coords[i + 1])))
        i += 2
    return pairs


def download_highways_congestions(HIGHWAYS_URL, CONGESTIONS_URL):
    # Creates a dictionary that collects the information from all available streets using the id of each highway as a key
    # and its description [0], coordinates [1] and congestion level [2] as a vector of values. Get the information from the "HIGHWAYS_URL" and "CONGESTIONS_URL" web links.
    highways_congestions = {}
    with urllib.request.urlopen(HIGHWAYS_URL) as response:
        lines = [l.decode('utf-8') for l in response.readlines()]
        reader = csv.reader(lines, delimiter=',')
        next(reader)
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
    # Draws all the streets in the "highways_congestions" dictionary on the map of barcelona in purple and save a ".png" file named "file".
    bcn_map = StaticMap(SIZE, SIZE)
    for key in highways_congestions:
        line = Line(highways_congestions.get(key)[1], 'rgb(153,51,255)', 2)
        bcn_map.add_line(line)
    image = bcn_map.render()
    image.save(file)


def choose_color(n):
    # Returns a color depending on the congestion level "n". Gray in case of not having information, black in case of the street being roofed
    # and blue, green, yellow, orange or red depending on if the street has very little congestion or much, being blue very little and red much.
    colors = ['rgb(128,128,128)', 'blue', 'green', 'rgb(255,255,0)', 'rgb(255,128,0)', 'red', 'rgb(0,0,0)']
    return colors[n]


def plot_congestions(highways_congestions, file, SIZE):
    # Draws all the streets in the "highways_congestions" dictionary on the map of barcelona with the color
    # chosen by the "choose_color" function and save a ".png" file named "file".
    bcn_map = StaticMap(SIZE, SIZE)
    for key in highways_congestions:
        line = Line(highways_congestions.get(key)[1], choose_color(int(highways_congestions.get(key)[2])), 4)
        bcn_map.add_line(line)
    image = bcn_map.render()
    image.save(file)


def itime(length, congestion, maxspeed):
    # Returns a value that relates the length, congestion level, and maximum speed of a street.
    if congestion == 6:
        return 1000000000
    return(length * 5 / (maxspeed * (6 - congestion)))


def get_nearest_node(graph, coord):
    # Finds the closest node to the pair of coordinates "coord" in a graph "graph".
    nearest_node = None
    distance = 100000000
    coords = (coord[1], coord[0])
    for node, info in graph.nodes.items():
        d = haversine((info['x'], info['y']), coords)
        if d < distance:
            distance = d
            nearest_node = node
    return nearest_node


def build_igraph(graph, highways_congestions):
    # Assigns its corresponding "itime" value at each edge of the graph "graph" that represents one of the streets that is
    # contained in the dictionary "highways_congestions".
    for key in highways_congestions:
        if highways_congestions.get(key)[2] != 0:
            start_coord = highways_congestions.get(key)[1][0]
            finish_coord = highways_congestions.get(key)[1][len(highways_congestions.get(key)[1]) - 1]
            start_node = get_nearest_node(graph, start_coord)
            finish_node = get_nearest_node(graph, finish_coord)
            try:
                list_nodes = osmnx.shortest_path(graph, start_node, finish_node)
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


def get_shortest_path_with_ispeeds(igraph, origin, destination):
    # Finds the shortest path between the "origin" and "destination" nodes based on the "itime" parameter.
    start = get_nearest_node(igraph, origin)
    finish = get_nearest_node(igraph, destination)
    return osmnx.shortest_path(igraph, start, finish, weight='itime')


def plot_path(igraph, ipath, SIZE, file):
    # Represents the path "ipath" on the map of barcelona in purple and saves a ".png" file with the name "file".
    bcn_map = StaticMap(SIZE, SIZE)
    for i in range(len(ipath) - 1):
        line = Line([(igraph.nodes[ipath[i]]['x'], igraph.nodes[ipath[i]]['y']), (igraph.nodes[ipath[i + 1]]['x'], igraph.nodes[ipath[i + 1]]['y'])], 'blue', 2)
        bcn_map.add_line(line)
    image = bcn_map.render()
    image.save(file)
