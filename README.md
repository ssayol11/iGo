# iGo
iGo is a telegram bot implemented in Python that shows the user the path from one location to another (both from Barcelona, Catalonia).
This path is computed keeping in mind the actual congestion of some highways from Barcelona and the intersections between them are represented in a graph, which computes the estimated time to go down each highway (or a segment of it). This compute is called 'itime', and each edge of the graph has its own.
## Installation
It's necessary to install the following libraries (also mentioned in the 'requirements.txt' file):
- 'osmnx' to download the graph
- 'urllib' to download/read files online
- 'networkx' to work with the graph
- 'staticmap' to represent the map and painting it
- 'python-telegram-bot' to interact with the module through telegram
- 'pickle' to read/write files from the computer
- 'haversine' to compute distances in the globe
- 'csv' to read files in CSV format
- 'random', 'datetime', 'telegram.ext' to the correct operation of the bot

'csv', 'pickle', 'random' and 'urllib' libraries are standard, no installation required to use them.

The libraries 'networkx', 'staticmap', 'python-telegram-bot' and 'haversine' can be installed using: 
- $ sudo pip3 install 'library name'

To install the 'osmnx' library:
  - Ubuntu:
    - $ sudo apt install libspatialindex-dev 
    - $ sudo pip3 install osmnx 
   
  - Mac: 
    - $ brew install spatialindex gdal 
    - $ pip3 install --upgrade pip setuptools wheel  
    - $ pip3 install --upgrade osmnx 
    - $ pip3 install --upgrade staticmap 
    - $ sudo pip3 install osmx
    
## Usage

## Support

For any queries regarding the project you can contact us at: 
  - Santi Sayol Pruna: santi.sayol@estudiantat.upc.edu
  - Roger Bel Clapés: roger.bel@estudiantat.upc.edu
  
