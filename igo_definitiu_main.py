import osmnx
import pickle
import urllib
import csv
import networkx
import collections
from haversine import haversine
from staticmap import StaticMap, Line
from easyinput import read

PLACE = 'Barcelona, Catalonia'
GRAPH_FILENAME = 'barcelona.graph'
SIZE = 800
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'

#Returns true if the graph named "GRAPH_FILENAME" is already downloaded or false otherwise.
def exist_graph(GRAPH_FILENAME):
    try:
        open(GRAPH_FILENAME)
        return True
    except:
        return False

#Download the simplified graph of the "PLACE" location using the osmnx library.
def download_graph(PLACE):
    graph = osmnx.graph_from_place(PLACE, network_type='drive', simplify=True)
    return graph

#Save the graph "graph" to a file named "GRAPH_FILENAME".
def save_graph(graph, GRAPH_FILENAME):
    with open(GRAPH_FILENAME, 'wb') as file:
        pickle.dump(graph, file)

#Load the graph "GRAPH_FILENAME" if it has been previously downloaded and saved.
def load_graph(GRAPH_FILENAME):
    with open(GRAPH_FILENAME, 'rb') as file:
        graph = pickle.load(file)
    return graph

#Converts the MultiDiGraph "graph" to a DiGraph using the "lenght" parameter to choose between parallel edges.
def download_digraph(graph):
    digraph = osmnx.get_digraph(graph, weight='length')
    return digraph

#Group in pairs the elements of a vector that contains an even number of decimal numbers.
def to_pairs(coordinates):
    coords = coordinates.split(',')
    pairs = []
    i = 0
    while i < len(coords):
        pairs.append((float(coords[i]), float(coords[i + 1])))
        i += 2
    return pairs

#Creates a dictionary that collects the information from all available streets using the id of each street as an identifier
#and its description, coordinates and congestion level as values. Get the information from the "HIGHWAYS_URL" and "CONGESTIONS_URL" web links.
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

#Draws all the streets in the "highways_congestions" dictionary on the map of barcelona in purple and save a ".png" file named "file".
def plot_highways(highways_congestions, file, SIZE):
    bcn_map = StaticMap(SIZE, SIZE)
    for key in highways_congestions:
        line = Line(highways_congestions.get(key)[1], 'rgb(153,51,255)', 2)
        bcn_map.add_line(line)
    image = bcn_map.render()
    image.save(file)

#Returns a color depending on the congestion level "n". Gray in case of not having information, black in case of the street being roofed
#and blue, green, yellow, orange or red depending on if the street has very little congestion or much, being blue very little and red much.
def choose_color(n):
    colors = ['rgb(128,128,128)', 'blue', 'green', 'rgb(255,255,0)', 'rgb(255,128,0)', 'red', 'rgb(0,0,0)']
    return colors[n]

#Draws all the streets in the "highways_congestions" dictionary on the map of barcelona with the color
#chosen by the "choose_color" function and save a ".png" file named "file".
def plot_congestions(highways_congestions, file, SIZE):
    bcn_map = StaticMap(SIZE, SIZE)
    for key in highways_congestions:
        line = Line(highways_congestions.get(key)[1], choose_color(int(highways_congestions.get(key)[2])), 4)
        bcn_map.add_line(line)
    image = bcn_map.render()
    image.save(file)

#Returns a value that relates the length, congestion level, and maximum speed of a street.
def itime(length, congestion, maxspeed):
    if congestion == 6:
        return 1000000000
    return(length * 5 / (maxspeed * (6 - congestion)))


#Finds the closest node to the pair of coordinates "coord" in a graph "graph".
def nearest_node(graph, coord):
    nearest_node = None
    nearest_dist = 99999
    coords = (coord[1], coord[0])

    for node, info in graph.nodes.items():
        d = haversine((info['x'], info['y']), coords)
        if d < nearest_dist:
            nearest_dist = d
            nearest_node = node
    return nearest_node

#Assigns its corresponding "itime" value at each edge of the graph "graph" that represents one of the streets that is
#contained in the dictionary "highways_congestions".
def build_igraph(graph, highways_congestions):

    for key in highways_congestions:
        if highways_congestions.get(key)[2] != 0 and highways_congestions.get(key)[2] != 6:
            start_coord = highways_congestions.get(key)[1][0]
            finish_coord = highways_congestions.get(key)[1][len(highways_congestions.get(key)[1]) - 1]
            start_node = nearest_node(graph, start_coord)
            finish_node = nearest_node(graph, finish_coord)
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

#Finds the shortest path between the "origin" and "destination" nodes based on the "itime" parameter.
def get_shortest_path_with_ispeeds(igraph, origin, destination):
    start = nearest_node(igraph, origin)
    finish = nearest_node(igraph, destination)
    return osmnx.shortest_path(igraph, start, finish, weight='itime')

#Represents the path "ipath" on the map of barcelona in purple and saves a ".png" file with the name "file".
def plot_path(igraph, ipath, SIZE, file):
    bcn_map = StaticMap(SIZE, SIZE)
    coords = []
    for i in range(len(ipath) - 1):
        coord = (igraph.nodes[ipath[i]]['x'], igraph.nodes[ipath[i]]['y'])
        coords.append(coord)
    line = Line(coords, 'rgb(153,51,255)', 2)
    bcn_map.add_line(line)
    image = bcn_map.render()
    image.save(file)

def main():
    # load/download graph (using cache)
    if exist_graph(GRAPH_FILENAME):
        graph = load_graph(GRAPH_FILENAME)
    else:
        graph = download_graph(PLACE)
        save_graph(graph, GRAPH_FILENAME)

    #osmnx.plot_graph(graph)

    highways_and_congestions = download_highways_congestions(HIGHWAYS_URL, CONGESTIONS_URL)
    plot_highways(highways_and_congestions, 'highways.png', SIZE)
    plot_congestions(highways_and_congestions, 'congestions.png', SIZE)

    #digraph = download_digraph(graph)

    igraph = build_igraph(graph,highways_and_congestions)

    ipath = get_shortest_path_with_ispeeds(igraph, osmnx.geocode('Cosmo Caixa, Barcelona'), osmnx.geocode('Sagrada Família, Barcelona'))

    plot_path(igraph, ipath, SIZE, 'ipath.png')

main()
