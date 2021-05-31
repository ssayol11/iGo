# importa l'API de Telegram
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
SUFIX = ', Barcelona, Catalonia'

time = datetime.datetime.now()

if igo.exist_graph(GRAPH_FILENAME):
    graph = igo.load_graph(GRAPH_FILENAME)
else:
    graph = igo.download_graph(PLACE)
    igo.save_graph(graph, GRAPH_FILENAME)

highways_and_congestions = igo.download_highways_congestions(HIGHWAYS_URL, CONGESTIONS_URL)
igraph = igo.load_graph('bot.igraph')

# defineix una funció que saluda i que s'executarà quan el bot rebi el missatge /start

def update_needed(context):
    new_time = datetime.datetime.now()
    if new_time > time + datetime.timedelta(minutes=5):
        time <- new_time
        return True
    return False

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Bot started")

def pos(update, context):
    lat, lon = float(context.args[0]), float(context.args[1])
    coords = (lat, lon)
    context.user_data['pos'] = coords
    print(context.user_data['pos'])

def where(update, context):
    try:
        lat, lon = update.message.location.latitude, update.message.location.longitude
        coords = (lat, lon)
        context.user_data['pos'] = coords
        file = "%d.png" % random.randint(1000000, 9999999)
        map = StaticMap(500, 500)
        map.add_marker(CircleMarker((lon, lat), 'blue', 10))
        image = map.render()
        image.save(file)
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(file, 'rb'))
        os.remove(file)
        print(context.user_data['pos'])
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Error, the location cannot be found. Share your location to use this module.')

def go(update, context):
    try:
        location = str(context.args[:])
        coords = osmnx.geocode(location + SUFIX)
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
    msg = "The available modules are:\n /start Starts the conversation and indicates when the bot is operative.\n /author Shows the author of the project.\n /where Shows your actual location in the map.\n /go [destination] Shows the path from your location to the destination you want to go."
    context.bot.send_message(chat_id=update.effective_chat.id, text=msg)

# declara una constant amb el access token que llegeix de token.txt
TOKEN = open('token.txt').read().strip()

# crea objectes per treballar amb Telegram
updater = Updater(token = TOKEN, use_context = True)
dispatcher = updater.dispatcher

# indica que quan el bot rebi la comanda /start s'executi la funció start
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('help', help))
dispatcher.add_handler(MessageHandler(Filters.location, where))
dispatcher.add_handler(CommandHandler('where', where))
dispatcher.add_handler(CommandHandler('go', go))
dispatcher.add_handler(CommandHandler('pos', pos))

# engega el bot
updater.start_polling()