import pandas as pd
import folium
from folium.plugins import HeatMapWithTime
from folium.plugins import MarkerCluster
import pandas as pd
import datetime
import git
import os
import webbrowser
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer

#Get the absolute path from root
path = os.path.dirname(os.path.abspath(__file__))
print(path)

#setup local server
PORT = 7000
HOST = '127.0.0.1'
SERVER_ADDRESS = '{host}:{port}'.format(host=HOST, port=PORT)
FULL_SERVER_ADDRESS = 'http://' + SERVER_ADDRESS

#Server handler
def TemproraryHttpServer(page_content_type, raw_data):
    """
    A simpe, temprorary http web server on the pure Python 3.
    It has features for processing pages with a XML or HTML content.
    """

    class HTTPServerRequestHandler(BaseHTTPRequestHandler):
        """
        An handler of request for the server, hosting XML-pages.
        """

        def do_GET(self):
            """Handle GET requests"""

            # response from page
            self.send_response(200)

            # set up headers for pages
            content_type = 'text/{0}'.format(page_content_type)
            self.send_header('Content-type', content_type)
            self.end_headers()

            # writing data on a page
            self.wfile.write(bytes(raw_data, encoding='utf'))

            return

    if page_content_type not in ['html', 'xml']:
        raise ValueError('This server can serve only HTML or XML pages.')

    page_content_type = page_content_type

    # kill a process, hosted on a localhost:PORT
    subprocess.call(['fuser', '-k', '{0}/tcp'.format(PORT)])

    # Started creating a temprorary http server.
    httpd = HTTPServer((HOST, PORT), HTTPServerRequestHandler)

    # run a temprorary http server
    httpd.serve_forever()

#Server runner
def run_html_server(html_data=None):

    if html_data is None:
        html_data = """
        <!DOCTYPE html>
        <html>
        <head>
        <title>Page Title</title>
        </head>
        <body>
        <h1>This is a Heading</h1>
        <p>This is a paragraph.</p>
        </body>
        </html>
        """

    # open in a browser URL and see a result
    webbrowser.open(FULL_SERVER_ADDRESS)

    # run server
    TemproraryHttpServer('html', html_data)

#update data from github
def update():
    today = datetime.datetime.now()
    today = today.strftime("%Y-%m-%d_%H:%m:%S")
    str = path + "/covid19br/cases-gps.csv"

    g = git.cmd.Git(path + "/covid19br")
    if(g.pull() == "Already up to date."):
        print("Nope!")
        f.write(today + " - Nope!\n")
    else:
        print("Updating!")
        f.write(today + " - Updating!\n")
        df = pd.read_csv(str)
        df_base = pd.read_csv(path +"/gps_dated/gps_dated.csv")
        df["date"] = today
        df_base.to_csv(path + "/gps_dated/gps_dated_last.bkp", index = False)
        df_base = df_base.append(df)
        df_base.to_csv(path + "/gps_dated/gps_dated.csv", index = False)
        f.write("Done!\n")
    generate_map(True)

# generate map from gps_dated data, if server True a local server will run
def generate_map(server = False):
    tmp = path + "/corona.html"

    df = pd.read_csv(path + '/gps_dated/gps_dated.csv')
    df = df.loc[df.index.repeat(df.total)]

    dates = df.date.unique()
    heat = []

    for i in dates:
        tmp_df = df.loc[df['date'] == i]
        tmp_heat = [[row["lat"], row["lon"]] for idx, row in tmp_df.iterrows()]
        heat.append(tmp_heat)

    folium_map = folium.Map(location=[df.lat.mean(), df.lon.mean()], zoom_start=4.4, attr="CoViD19 no Brasil Agora")

    folium_map.add_child(HeatMapWithTime(heat,
            index = list(dates),
            auto_play = True,
            name='Coronavirus'))

    for i in dates:
        tmp_df = df.loc[df['date'] == i]
        mk = MarkerCluster(name='Cluster ' + i,
        show=False)
        for lat, lon in zip(tmp_df.lat, tmp_df.lon):
            folium.CircleMarker(location=[lat, lon], radius = (10)/2,
            fill_opacity = 0.9,
            fill_color='#3186cc',
            ).add_to(mk)
        folium_map.add_child(mk)
    folium_map.add_child(folium.LayerControl())

    f.write("Saving html...\n")
    try:
        folium_map.save(tmp)
        f.write("Saved!\n")
    except:
        f.write("Error in saving process!!!\n")

    if(server):
        with open(tmp) as fi:
            folium_map_html = fi.read()
        run_html_server(folium_map_html)

f = open(path+'/log.txt', "a+")
update()
f.close()
