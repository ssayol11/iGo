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

def main():
    # load/download graph (using cache)
    try:
        graph = load_graph(GRAPH_FILENAME)
    except:
        graph = download_graph(PLACE)
        save_graph (graph, GRAPH_FILENAME)

    #osmnx.plot_graph(graph)

    highways_and_congestions = download_highways_congestions(HIGHWAYS_URL, CONGESTIONS_URL)
    plot_highways(highways_and_congestions, 'highways.png', SIZE)
    plot_congestions(highways_and_congestions, 'congestions.png', SIZE)

main()
