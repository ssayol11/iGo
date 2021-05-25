from telegram.ext import Updater, CommandHandler
import igo

HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'
SIZE = 800

# defineix una funció que saluda i que s'executarà quan el bot rebi el missatge /start
def start(update, context):
    congestions = igo.download_highways_congestions(HIGHWAYS_URL, CONGESTIONS_URL)
    igo.plot_congestions(congestions, 'congestions.png', SIZE)
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('congestions.png', 'rb'))

def help(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="/author (owners of the project)")
    context.bot.send_message(chat_id=update.effective_chat.id, text="/go destination (shows the way to the destination)")
    context.bot.send_message(chat_id=update.effective_chat.id, text="/where (shows the actual position of the user)")

# declara una constant amb el access token que llegeix de token.txt
TOKEN = open('token.txt').read().strip()

# crea objectes per treballar amb Telegram
updater = Updater(token = TOKEN, use_context = True)
dispatcher = updater.dispatcher

# indica que quan el bot rebi la comanda /start s'executi la funció start
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('help', help))

# engega el bot
updater.start_polling()
