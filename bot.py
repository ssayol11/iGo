from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import random
from staticmap import StaticMap, CircleMarker
import os
import osmnx
import datetime
import igo

PLACE = 'Barcelona, Catalonia'
GRAPH_FILENAME = 'barcelona.graph'
SIZE = 800
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'

global time
time = datetime.datetime.now()

if igo.exist_graph(GRAPH_FILENAME):
    graph = igo.load_graph(GRAPH_FILENAME)
else:
    graph = igo.download_graph(PLACE)
    igo.save_graph(graph, GRAPH_FILENAME)

global highways_and_congestions
highways_and_congestions = igo.download_highways_congestions(HIGHWAYS_URL, CONGESTIONS_URL)

global igraph
igraph = igo.build_igraph(graph, highways_and_congestions)


def update_needed(context):
    # Checks if 5 minutes have passed since the bot started (it resets the igraph every 5 minutes).
    new_time = datetime.datetime.now()
    if new_time > time + datetime.timedelta(minutes=5):
        time <- new_time
        return True
    return False


def start(update, context):
    # Indicates when the bot is operative.
    context.bot.send_message(chat_id=update.effective_chat.id, text="iGo bot started")


def pos(update, context):
    # Stablishes a virtual ubication.
    lat, lon = float(context.args[0]), float(context.args[1])
    coords = (lat, lon)
    context.user_data['pos'] = coords


def save_location(update, context):
    lat, lon = update.message.location.latitude, update.message.location.longitude
    coords = (lat, lon)
    context.user_data['pos'] = coords


def where(update, context):
    # Returns a map with the actual location of the user and saves its coordinates in a dictionary.
    try:
        file = "%d.png" % random.randint(1000000, 9999999)
        map = StaticMap(500, 500)
        map.add_marker(CircleMarker((context.user_data['pos'][1], context.user_data['pos'][0]), 'blue', 10))
        image = map.render()
        image.save(file)
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(file, 'rb'))
        os.remove(file)
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Error, the location cannot be found. Share your location to use this module.')


def go(update, context):
    # Returns a map with de shortest path (in time) from the user's location to the destination.
    try:
        location = ""
        for arg in context.args:
            location = location + ' ' + arg
        coords = osmnx.geocode(location)
        if update_needed(context):
            highways_and_congestions <- igo.download_highways_congestions
            igraph <- igo.build_igraph(graph, highways_and_congestions)
        ipath = igo.get_shortest_path_with_ispeeds(igraph, context.user_data['pos'], coords)
        file = "%d.png" % random.randint(1000000, 9999999)
        igo.plot_path(igraph, ipath, SIZE, file)
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(file, 'rb'))
        os.remove(file)
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Error, there is no available path.')


def help(update, context):
    # Briefly explains the commands available in the bot.
    msg = "The available modules are:\n /start Starts the conversation and indicates when the bot is operative.\n /authors Shows the authors of the project.\n /where Shows your actual location in the map.\n /go [destination] Shows the path from your location to the destination you want to go."
    context.bot.send_message(chat_id=update.effective_chat.id, text=msg)


def authors(update, context):
    # Shows the names and the studies of the authors of this project (iGo and Bot).
    msg = "The authors of this project are: Roger Bel Clapés and Santi Sayol Pruna, from GCED - UPC"
    context.bot.send_message(chat_id=update.effective_chat.id, text=msg)


# declares the constant TOKEN than ables the code to acces the bot
TOKEN = open('token.txt').read().strip()

# some objects are created to work with Telegram
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

# some commands are stablished
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('help', help))
dispatcher.add_handler(MessageHandler(Filters.location, save_location))
dispatcher.add_handler(CommandHandler('where', where))
dispatcher.add_handler(CommandHandler('go', go))
dispatcher.add_handler(CommandHandler('pos', pos))
dispatcher.add_handler(CommandHandler('authors', authors))

# toggles the bot
updater.start_polling()
