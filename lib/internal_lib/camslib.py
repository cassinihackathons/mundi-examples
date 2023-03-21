#!/usr/bin/python
# -*- coding: ISO-8859-15 -*-
# =============================================================================
# Copyright (c) 2019 Mundi Web Services
# Licensed under the 3-Clause BSD License; you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
# https://opensource.org/licenses/BSD-3-Clause
#
# Author : Loona Nouvellon / Guillaume Lenoir d'Espinasse
#
# Contact email: loona.nouvellon@atos.net
# =============================================================================

import datetime
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import timedelta
from matplotlib.colors import ListedColormap
from matplotlib.pyplot import figure
os.environ["PROJ_LIB"] = r"/opt/conda/share/proj"
from mpl_toolkits.basemap import Basemap
from PIL import Image

import string
import requests
import ipywidgets as widgets
from IPython.display import display, clear_output

from owslib.wcs import WebCoverageService
from owslib.wms import WebMapService

from ecmwfapi import ECMWFDataServer
import ecmwfapi

from IPython.display import Image
import glob

from IPython.display import clear_output, HTML, Image
from PIL import Image, ImageDraw, ImageFont, ImageOps
import pygrib
import imageio
from tqdm import tqdm

from os import path

server_url = "https://geoservices.regional.atmosphere.copernicus.eu/services/"
dlserver = "https://download.regional.atmosphere.copernicus.eu/services/CAMS50?"
    
methods = ["FORECAST", "ANALYSIS"]
pollens = ["BIRCHPOLLEN", "OLIVEPOLLEN", "GRASSPOLLEN", "RAGWEEDPOLLEN"]
species = ["O3", "CO", "NH3", "NO", "NO2", "NMVOC", "PANs", "PM10", "PM2.5", "SO2" ] + pollens
models = ["ENSEMBLE", "CHIMERE", "EMEP", "EURAD", "LOTOSEUROS", "MATCH", "MOCAGE", "SILAM"]
levels = [0,  50, 250, 500, 1000, 2000, 3000, 5000]

dict_projection_map = ["WORLD","AFRICA", "ASIA", "EUROPE","NORTH-AMERICA","NORTH-POLE", "OCEANIA", "SOUTH-AMERICA","SOUTH-POLE"]

dict_color_map = ['ocean', 'gist_earth', 'terrain', 'gist_stern','gnuplot', 'gnuplot2',
                  'CMRmap', 'brg','hsv', 'jet', 'nipy_spectral', 'gist_ncar',  'tab20b', 'tab20c']

color_display_direction = ["Left to right", "Right to left"]

data_parameters = ["Nitrogen dioxyde", "Ozone", "Sulfur dioxyde", "Particulate Matter <2.5 um", "Particulate Matter <10 um" ]

SAVE_FOLDER_IMAGES = "/home/jovyan/work/cams_data/cams_ecmwfapi/images_data/"
SAVE_FOLDER_GIF = "/home/jovyan/work/cams_data/cams_ecmwfapi/"


# ----------------------------------------------------------------
#  CAMS ECMWFAPI notebook functions:
# ----------------------------------------------------------------

def setup_dir():
    """This function gets the destination folder path"""
    output_dir = path.join(os.environ['HOME'], 'work/cams_data/cams_ecmwfapi/images_data/')

    return output_dir


def setup(output_dir):
    """This function creates the folder output_dir if it doesn't exist"""

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_filename = path.join(output_dir, 'output.grib')

    return output_filename


def configure_ecmwfapi():
    """This function allows to log onto the ecmwfapi service"""

    ecmwfapi_email_widget = widgets.Text(
        value='',
        placeholder='Enter your email to log in ECMWF',
        description='Your Email',
        disabled=False
    )

    ecmwfapi_key_widget = widgets.Text(
        value='',
        placeholder='Enter your ECMWF Key',
        description='Your Key',
        disabled=False
    )

    button_widget = widgets.Button(
        description='Validate',
        disabled=False,
        button_style='',
        tooltip='Click me',
    )

    output_widget = widgets.Output(
    )

    display(ecmwfapi_email_widget)
    display(ecmwfapi_key_widget)
    display(button_widget)
    display(output_widget)

    def click_configure_ecmwfapi(b):
        with output_widget:
            ecmwf_email = ecmwfapi_email_widget.value
            ecmwf_key = ecmwfapi_key_widget.value
            print('Your ECMWF login email is : ' + ecmwf_email + ', and your ECMWF Key is : ' + ecmwf_key)
            content = f'{{\n    "url"   : "https://api.ecmwf.int/v1",\n    "key"   : "{ecmwf_key}",\n    "email" : "{ecmwf_email}"\n}}'
            # write content to $HOME/.ecmwfapirc
            with open(path.join(os.environ["HOME"], '.ecmwfapirc'), 'w') as f:
                f.write(content)

    button_widget.on_click(click_configure_ecmwfapi)


def request_ecmwfapi(output_filename):
    """This function creates a request to the ECMWFAPI service with parameters asked in the GUI
    and generates the output.grib file containing resulting data.

    Parameters
    ----------
    output_filename: string
        folder where the output.grib file will be stored
    """

    data_parameter_widget = widgets.Dropdown(
        options=data_parameters,
        description='Data selection',
    )

    start_date_widget = widgets.DatePicker(
        description='Starting Date',
        value=datetime.date.today() - datetime.timedelta(45),
        disabled=False
    )

    current_date_widget = widgets.DatePicker(
        description='Final date',
        value=datetime.date.today() - datetime.timedelta(15),
        disabled=False)

    hour_06 = widgets.Checkbox(
        value=False,
        description='06:00:00',
        disabled=False,
        indent=True
    )

    hour_12 = widgets.Checkbox(
        value=False,
        description='12:00:00',
        disabled=False,
        indent=True
    )

    hour_18 = widgets.Checkbox(
        value=False,
        description='18:00:00',
        disabled=False,
        indent=True
    )

    label_hour = widgets.VBox([widgets.Label(value="Select one or many hours below :"), hour_06, hour_12, hour_18])
    button = widgets.Button(description='Validate')
    out = widgets.Output()

    display(data_parameter_widget)
    display(start_date_widget)
    display(current_date_widget)
    display(label_hour)
    display(button)
    display(out)

    def click_ecmwfapi_request(b):
        with out:
            time_6 = ""
            time_12 = ""
            time_18 = ""
            if hour_06.value == True:
                time_6 = "/06:00:00"
            if hour_12.value == True:
                time_12 = "/12:00:00"
            if hour_18.value == True:
                time_18 = "/18:00:00"

            time_param = time_6 + time_12 + time_18

            server = ecmwfapi.ECMWFDataServer()
            server.retrieve({
                "class": "mc",
                "dataset": "cams_nrealtime",
                "date": str(start_date_widget.value) + "/to/" + str(current_date_widget.value),
                "expver": "0001",
                "levtype": "sfc",
                "param": parameter_value(data_parameter_widget.value),
                "step": "0",
                "stream": "oper",
                "time": "00:00:00" + time_param,
                "type": "an",
                "target": output_filename,
            })

    button.on_click(click_ecmwfapi_request)


def parameter_value(atmosphere_data_parameter):
    """This function returns the parameter value corresponding to the athmosphere gaz value selected in the GUI.

    Parameters
    ----------
    atmosphere_data_parameter: string
        Atmosphere data parameter selected.

    Returns
    -------
    data_param: string
        The data parameter value used in the ECMWFAPI request
    """

    if atmosphere_data_parameter == "Nitrogen dioxyde":
        data_param = "125.210"
    elif atmosphere_data_parameter == "Ozone":
        data_param = "206.210"
    elif atmosphere_data_parameter == "Sulfur dioxyde":
        data_param = "126.210"
    elif atmosphere_data_parameter == "Particulate Matter <2.5 um":
        data_param = "73.210"
    elif atmosphere_data_parameter == "Particulate Matter <10 um":
        data_param = "74.210"

    return data_param


def get_projection_map(output_dir, output_filename):
    """ This function allows to define what kind of projection map the user wants to display data

     Parameters
    ----------
    output_dir: string
        folder where output.grib and img are stored.
    output_filename : string
        output.grib location
    """

    projection_widget = widgets.Dropdown(
        options=dict_projection_map,
        description='Map Location',
    )

    button = widgets.Button(description='Validate')
    out = widgets.Output()

    display(projection_widget)
    display(button)
    display(out)

    def click_projection_map(b):
        with out:
            clear_output(wait=True)
            get_color_map(output_dir, output_filename, projection_widget.value)

    button.on_click(click_projection_map)


def get_color_map(output_dir, output_filename, projection):
    """ This function allows to display the Matplotlib colormap possibilities and gives the right to the user to define
    what kind of colormap and direction way he wants to display data.

    Parameters
    ----------
    output_dir: string
        folder where output.grib and img are stored.
    output_filename : string
        output.grib location
    projection : string
        the continent where data will be displayed
    """

    # displaying colormaps sample:
    gradient = np.linspace(0, 1, 256)
    gradient = np.vstack((gradient, gradient))

    fig, axes = plt.subplots(nrows=len(dict_color_map))
    fig.subplots_adjust(top=0.95, bottom=0.01, left=0.2, right=0.99)
    axes[0].set_title('Colormaps sample', fontsize=14)

    for ax, name in zip(axes, dict_color_map):
        ax.imshow(gradient, aspect='auto', cmap=plt.get_cmap(name))
        pos = list(ax.get_position().bounds)
        x_text = pos[0] - 0.01
        y_text = pos[1] + pos[3] / 2.
        fig.text(x_text, y_text, name, va='center', ha='right', fontsize=10)

    # Turn off *all* ticks & spines, not just the ones with colormaps.
    for ax in axes:
        ax.set_axis_off()

    plt.show()

    # defining colormap user choice:
    color_map_widget = widgets.Dropdown(
        options=dict_color_map,
        description='Map colors',
        value="gist_ncar"
    )

    color_display_direction_widget = widgets.Dropdown(
        options=color_display_direction,
        description='Display direction',
    )

    image_title_widget = widgets.Text(
        value='',
        placeholder='Enter your title',
        description='Title',
        disabled=False
    )

    gif_filename_widget = widgets.Text(
        value='',
        placeholder='Enter the GIF file name',
        description='GIF file name',
        disabled=False
    )

    button = widgets.Button(description='Validate')
    out = widgets.Output()

    display(color_map_widget)
    display(color_display_direction_widget)
    display(image_title_widget)
    display(gif_filename_widget)
    display(button)
    display(out)

    def click_color_map(b):
        with out:
            color_map = color_map_widget.value
            if color_display_direction_widget.value == color_display_direction[1]:
                color_map = color_map + "_r"
            if (image_title_widget.value == '') and (gif_filename_widget.value == ''):
                gif_filename_widget.value = "your_gif_file"
            elif (gif_filename_widget.value == ''):
                gif_filename_widget.value = image_title_widget.value
            print("Images download is starting !")
            clear_output(wait=True)
            download_images(output_filename, output_dir, projection, color_map, image_title_widget.value,
                            gif_filename_widget.value)

    button.on_click(click_color_map)


def download_images(output_filename, output_dir, projection, color_map, image_title, gif_filename):
    """ This function allows to download the data in the output.grib file and build each image

    Parameters
    ----------
    output_dir: string
        folder where output.grib and img are stored.
    output_filename : string
        output.grib location
    projection : string
        the continent where data will be displayed
    color_map : string
        the color range selected to display data
    image_title : string
        the title displayed on each image
    gif_filename : string
        the name of the gif file
    """

    # open a GRIB file
    with pygrib.open(output_filename) as grbs:
        grb = grbs.select()[0]
        vmax = np.amax(grb.values)

        unit = grb['units']

        # get the longitudes and the latitudes
        latitudes, longitudes = grb.latlons()

        # Emptying the folder which contains precedent img
        if not os.path.exists("/home/jovyan/work/cams_data/cams_ecmwfapi/images_data/"):
            os.makedirs("/home/jovyan/work/cams_data/cams_ecmwfapi/images_data/")
        files = glob.glob(f'{"/home/jovyan/work/cams_data/cams_ecmwfapi/images_data/"}[!output.grib]*')
        for f in files:
            os.remove(f)

        cpt = 1

        # create and save a figure for each grib message
        for grb in grbs.select():
            figure(num=None, figsize=(16, 10))

            # create a map
            map_ = get_basemap(projection, grb)
            map_.drawcoastlines()
            map_.drawcountries()

            x, y = map_(longitudes, latitudes)
            data = grb.values

            # display the data
            cs = map_.pcolormesh(x, y, data, cmap=plt.get_cmap(color_map), vmin=0, vmax=vmax)
            map_.colorbar(cs, label=unit)

            plt.title(str(image_title) + f' / {grb["parameterName"]} / date: {grb["dataDate"]} / hour: {grb["hour"]}',
                      loc='left')
            plt.savefig(path.join(output_dir, f'{grb.messagenumber}'))
            plt.close()
            print("\r #Image - " + str(cpt) + "/" + str(np.size(grbs.select())) + " downloaded")
            cpt += 1
            clear_output(wait=True)

    print("Your img have been successfully downloaded !")
    display_GIF_images(output_dir, gif_filename)


def get_basemap(projection, grb):
    """ This function returns the Basemap corresponding to the projection map selected in the GUI.

    Parameters
    ----------
    projection : string
        the continent where data will be displayed

    Returns
    -------
    map_:
        the Basemap builds to display data
    """

    # get the longitudes and the latitudes
    latitudes, longitudes = grb.latlons()

    if projection == "WORLD":
        map_ = Basemap(projection='cyl', lat_ts=10, llcrnrlon=longitudes.min(),
                       urcrnrlon=longitudes.max(), llcrnrlat=latitudes.min(), urcrnrlat=latitudes.max(), resolution='l')
    elif projection == "AFRICA":
        map_ = Basemap(width=12000000, height=9000000, resolution='l', projection='eqdc', lat_1=-45., lat_2=36, lat_0=0,
                       lon_0=22.)
    elif projection == "SOUTH-AMERICA":
        map_ = Basemap(width=12000000, height=9000000, resolution='l', projection='eqdc', lat_1=-55., lat_2=12,
                       lat_0=-26, lon_0=-60.)
    elif projection == "ASIA":
        map_ = Basemap(width=12000000, height=9000000, resolution='l', projection='eqdc', lat_1=10., lat_2=70, lat_0=45,
                       lon_0=100.)
    elif projection == "EUROPE":
        map_ = Basemap(width=8000000, height=7000000, resolution='l', projection='eqdc', lat_1=40., lat_2=60, lon_0=35,
                       lat_0=50)
    elif projection == "NORTH-AMERICA":
        map_ = Basemap(width=12000000, height=9000000, resolution='l', projection='eqdc', lat_1=45., lat_2=55, lat_0=50,
                       lon_0=-107.)
    elif projection == "NORTH-POLE":
        map_ = Basemap(projection='nplaea', boundinglat=10, lon_0=270, resolution='l')
    elif projection == "OCEANIA":
        map_ = Basemap(width=12000000, height=9000000, resolution='l', projection='eqdc', lat_1=-45., lat_2=5,
                       lat_0=-25, lon_0=136.)
    elif projection == "SOUTH-POLE":
        map_ = Basemap(projection='splaea', boundinglat=-10, lon_0=90, resolution='l')

    return map_


def display_GIF_images(output_dir, gif_filename):
    """ This function allows to build and display the GIF file.

    Parameters
    ----------
    output_dir: string
        folder where output.grib and img are stored.
    output_filename : string
        output.grib location
    """

    images = []
    accepted_extensions = ["png"]
    filenames = [fn for fn in os.listdir(SAVE_FOLDER_IMAGES) if fn.split(".")[-1] in accepted_extensions]
    temp = [int(fn.split('.')[0]) for fn in filenames]
    temp = sorted(temp)
    final_filenames = [f'{elt}.png' for elt in temp]
    k = len(final_filenames)
    cpt = 1
    for file in final_filenames:
        print("\r Image #" + str(cpt) + "/" + str(k))
        image = Image.open(f"{SAVE_FOLDER_IMAGES}{file}")
        image = image.convert('RGB')
        images.append(np.array(image))
        cpt += 1
        clear_output(wait=True)

    # Repeating the last image x times to have a stop at the end of the GIF
    last_image = images[-1]
    for i in range(4):
        images.append(np.array(last_image))

    imageio.mimsave(f'{SAVE_FOLDER_GIF}{gif_filename}.gif', images, duration=0.3)
    clear_output(wait=True)
    print("GIF File Generated")
    display(HTML('<img src="{}">'.format('../../work/cams_data/cams_ecmwfapi/' + gif_filename + '.gif')))


def display_gif_folder():
    """ This function allows to display GIF files presents in the cams_ecmwfapi folder
    """

    accepted_extensions = ["gif"]
    filenames = [fn for fn in os.listdir(SAVE_FOLDER_GIF) if fn.split(".")[-1] in accepted_extensions]
    display_file_widget = widgets.Dropdown(
        options=filenames,
        description='GIF Display',
    )
    button_dis = widgets.Button(description='Display this GIF')
    out_wid_dis = widgets.Output()

    def click_display(b):
        with out_wid_dis:
            clear_output(wait=True)
            print('Your "' + display_file_widget.value + '" is being displayed !')
            print("")
            display(HTML('<img src="{}">'.format('../../work/cams_data/cams_ecmwfapi/' + display_file_widget.value)))

    button_dis.on_click(click_display)

    display(display_file_widget)
    display(button_dis)
    display(out_wid_dis)

# ----------------------------------------------------------------
#  CAMS methods
# ----------------------------------------------------------------

def getServiceUrl(method, model, service, token):
    if model in models and method in methods:
        return server_url + "CAMS50-" + model + "-" + method +"-01-EUROPE-" + service  + "?token=" + token

# get your token
def getToken(username, password):
    response = requests.get(server_url + "GetAPIKey?username=" + username + "&password=" + password)
    return response.text.replace('<', '>').split('>')[2]

# display a map from a grib file
def plotGrib(grb, title, vmin = None, vmax = None, bbox=None, cmap=None):
    if bbox!=None:
        data, lats, lons = grb.data(lon1= bbox[0], lon2=bbox[2], lat1=bbox[1],lat2=bbox[3])
    else:
        data = grb.values
        lats,lons = grb.latlons() #Get the longitudes and the latitudes of the Grib file

    #Set the unit
    unit = 'kg/m3'
    if species in pollens:
        unit = 'm-3'

    figure(num=None, figsize=(14, 8))

    #Create a basemap with the coordinates of the bbox
    m=Basemap(projection='cyl',lat_ts=10,llcrnrlon=lons.min(), \
      urcrnrlon=lons.max(),llcrnrlat=lats.min(),urcrnrlat=lats.max(), \
      resolution='l') 

    x, y = m(lons, lats)

    m.drawcoastlines()
    m.drawcountries()

    m.bluemarble()
    
    #List of colors used for the colormap
    cols = [(0, 0, 0, 0), (0.01,0.36,0.82), (0,0.5,1), \
            (0,1,1), (0,1,0.5), (0,1,0), (0.5,1,0), (1,1,0), \
            (0.94, 0.6, 0.06), (1,0.5,0), (0.9,0.24,0), (1,0,0)]

    #Create a colormap
    cmap = ListedColormap(cols)
    
    #Color the map
    if vmin == None:
        vmin = np.amin(grb.values)
    if vmax == None:
        vmax = np.amax(grb.values)
        
    levels = np.linspace(vmin, vmax, 100)
    cs = m.contourf(x, y, data, levels, cmap = cmap, vmin=vmin, vmax = vmax, norm = colors.PowerNorm(gamma=2/3)) 
    
    #Put a title to the figure
    plt.title(title) 

    #Display the colorbar
    clb = plt.colorbar(cs,orientation='vertical', label=unit) 

    #Display the map
    return(plt)

#Define the widgets for the geographical area
def geographical_area_tab():
    lonmin= widgets.FloatText(value=-24.95, description='Long min:', step=0.01) 
    latmin= widgets.FloatText(value= 30.05, description='Lat min:', step=0.01) 
    lonmax= widgets.FloatText(value=44.95, description='Long max:', step=0.01) 
    latmax= widgets.FloatText(value=69.95, description='Lat max:', step=0.01) 

    bbox_menu = widgets.VBox([lonmin, latmin, lonmax, latmax])
    country_menu = widgets.Text(placeholder='Ex: Germany, Spain...')

    children = [bbox_menu, widgets.VBox([widgets.Label(value="Enter a country:"), country_menu])]

    tab = widgets.Tab()
    tab.children = children
    tab.set_title(0,'Bounding Box')
    tab.set_title(1,'Country')
    return tab, lonmin, latmin, lonmax, latmax, country_menu


# ----------------------------------------------------------------
#  CAMS Web Coverage Service class
# ----------------------------------------------------------------
class cams_wcs():

    # Download a coverage in Grib 
    def downloadCoverage(wcs, id, time, _subsets_, filename):
        #Get the data
        output = wcs.getCoverage(identifier=[id],
                              grid=0.1,
                              subset='time(' + time + ')',
                              subsets=_subsets_,
                              format='application/x-grib')

        #Get the destination folder path
        dir = '/home/jovyan/work/cams_data/cams_europe_services/02_WCS_example/'

        #Create the folder if it doesn't exist
        if not os.path.exists(dir):
            os.makedirs(dir)
            
        #Create a file
        f = open(os.path.join(dir, filename),'wb')
        f.write(output.read())
        f.close()
    
    
    def displayMap(method, model, token):

        url = getServiceUrl(method, model, 'WCS', token)
        wcs = WebCoverageService(url, version='2.0.1')

        layers_menu = widgets.Dropdown(
            options=list(wcs.contents),
            value=list(wcs.contents)[0],
            description='Layer:',
            disabled=False,
        )

        def getValidDates(lay):
            gml = '{http://www.opengis.net/gml/3.2}'
            layer = wcs.contents[lay]
            descCov = wcs.getDescribeCoverage(lay)

            def timePosition(pos):
                #Find the time position in Describe Coverage
                pos = descCov[0].find( gml + 'boundedBy/' + gml +'EnvelopeWithTimePeriod/' + gml + pos).text
                #Return the respective date
                return datetime.datetime.strptime(pos.replace('.', ':'), '%Y-%m-%dT%H:%M:%SZ')

            #Get the begin and end positions
            dt = timePosition('beginPosition')
            enddt = timePosition('endPosition')

            #Get all valid dates
            validDates = []
            while dt <= enddt:
                validDates.append(dt)
                dt = dt + timedelta(hours=1)
            return validDates

        def getAltitudes(lay):
            layer = wcs.contents[lay]
            descCov = wcs.getDescribeCoverage(lay) 
            gml = '{http://www.opengis.net/gml/3.2}'

            #Select an altitude only if dimension = 4
            altitudes = [0]
            if layer.grid.dimension == 4:
                rgrid = '{http://www.opengis.net/gml/3.3/rgrid}'
                coefficients = descCov[0].findall(gml + 'domainSet/' + rgrid + 'ReferenceableGridByVectors/' + rgrid + 'generalGridAxis')[2].find( rgrid + 'GeneralGridAxis/' + rgrid + 'coefficients')
                altitudes = coefficients.text.split(' ')
            return altitudes

        layer_name =  layers_menu.value
        validDates = getValidDates(layer_name)

        times_menu = widgets.Dropdown(
            options=validDates,
            value=validDates[0],
            description='Validity time:',
            disabled=False,
        )

        heigth_menu = widgets.Dropdown(
            options= getAltitudes(layer_name),
            value=getAltitudes(layer_name)[0],
            description='Altitude :',
            disabled=False,
        )

        def handle_layers_menu_change(change):
            times_menu.options=getValidDates(change.new)
            times_menu.value=getValidDates(change.new)[0] 
            heigth_menu.options=getAltitudes(change.new)
            heigth_menu.value=getAltitudes(change.new)[0] 

        layers_menu.observe(handle_layers_menu_change, names='value')

        display(layers_menu, times_menu, heigth_menu)
    
        tab, lonmin, latmin, lonmax, latmax, country_menu = geographical_area_tab()
        display(widgets.Label(value="Select a geographical area in Europe:"), tab)

        #Display the validate button
        out=widgets.Output()
        button=widgets.Button(description='Validate')
        vbox=widgets.VBox([button, out])
        display(vbox)

        def click(b):
            layer_name = layers_menu.value
            layer = wcs.contents[layer_name]

            #Define request parameters
            time = datetime.datetime.strftime( times_menu.value,'%Y-%m-%dT%H:%M:%SZ')

            #Define the bbox with the selected values
            if (tab.selected_index == 0):
                bbox = (lonmin.value, latmin.value, lonmax.value, latmax.value)
            else:
                 polygon, bbox = polygon_bbox_country(country_menu.value)
            
            subsets = [('lat',bbox[1],bbox[3]), ('long',bbox[0],bbox[2])]
            
            if (layer.grid.dimension == 4):
                subsets.append(('height', heigth_menu.value))

            dir = '/home/jovyan/work/cams_data/cams_europe_services/02_WCS_example/'
            name = model + '_' + method + '_' + layer_name + '.grib' 
            filename = os.path.join(dir, name)

            #Download the data
            cams_wcs.downloadCoverage(wcs, layer_name, time, subsets, filename)

            import pygrib
            grib = dir +'/' + name
            grbs = pygrib.open(grib)
            grb = grbs.select()[0]

            with out:
                plt.close()
                clear_output()
                plotGrib(grb, layer_name.replace('_', ' ')).show()

        button.on_click(click)

# ----------------------------------------------------------------
#  CAMS Web Map Service class
# ----------------------------------------------------------------
class cams_wms():
    
    def getMapImage(wms, layer, bbox, size, time, elevation):
        #Get the map
        output = wms.getmap(layers = [layer.name], 
                         styles = layer.styles, 
                         srs = layer.crsOptions[0], 
                         bbox = bbox, 
                         size = size, 
                         time = time, 
                         elevation = elevation,
                         format = 'image/png')

        #Open the image
        return(Image.open(output))

    def getLegend(layer):
        from io import BytesIO

        #Get the style's name
        key = list(layer.styles.keys())[0]

        #Get the legend
        resp = requests.get(layer.styles.get(key).get('legend'))

        #Open the image
        return(Image.open(BytesIO(resp.content)))
    
    def plotMapLegend(image, legendImg, title, bbox):
        fig = plt.figure(figsize=(10, 6))

        fig.subplots_adjust(0, 0, 6, 4)
        #Create a Basemap
        m =  Basemap(projection='cyl', llcrnrlon=bbox[0], 
                       llcrnrlat=bbox[1], urcrnrlon=bbox[2],
                       urcrnrlat=bbox[3], epsg=4326, resolution='l') 

        m.drawcoastlines()
        m.drawcountries()
        
        #Display the image over the map
        m.imshow(np.array(image.transpose(Image.FLIP_TOP_BOTTOM)))

        #Put a title to the map
        plt.title(title, fontsize=20)

        #Add the legend
        fig.subplots_adjust(0, 0, 1, 1)
        legend = fig.add_axes([0., 0., 2.5, 1])
        legend.imshow(legendImg, origin = 'upper')
        legend.set_xticks([])
        legend.set_yticks([])

        return plt

    def displayMap(method, model, token):
        
        url = getServiceUrl(method, model, 'WMS', token)
        wms = WebMapService(url, version='1.3.0')

        layers_menu = widgets.Dropdown(
            options=list(wms.contents),
            value=list(wms.contents)[0],
            description='Layer:',
            disabled=False,
        )

        display(layers_menu)

        layer =  wms.contents[layers_menu.value]
        
        #Display the valid dates
        times_menu = widgets.Dropdown(
            options=layer.timepositions,
            value=layer.timepositions[0],
            description='Validity time:',
            disabled=False,
        )

        #Choose an elevation only if elevations is not None
        elevations = [0]
        if layer.elevations != None: 
            elevations = layer.elevations

        elevations_menu = widgets.Dropdown(
            options=elevations,
            value=elevations[0],
            description='Elevation:',
            disabled=False,
        )

        height_menu = widgets.IntText(
            value=495,
            description='Height:',
            disabled=False)

        width_menu = widgets.IntText(
            value=810,
            description='Width:',
            disabled=False)

        def handle_layers_menu_change(change):
            layer =  wms.contents[change.new]

            times_menu.options=layer.timepositions
            times_menu.value= layer.timepositions[0] 

            elevations = [0]
            if layer.elevations != None:
                elevations = layer.elevations
            elevations_menu.options=elevations
            elevations_menu.value=elevations[0]

        layers_menu.observe(handle_layers_menu_change, names='value')

        display(times_menu, elevations_menu, widgets.VBox([widgets.Label(value="Choose the image size:"), height_menu, width_menu]))

        tab, lonmin, latmin, lonmax, latmax, country_menu = geographical_area_tab()

        display(widgets.Label(value="Select a geographical area in Europe:"), tab)

        #Display the validate button
        out=widgets.Output()
        button=widgets.Button(description='Validate')
        vbox=widgets.VBox([button, out])
        display(vbox)

        def click(b):
            layer = wms.contents[layers_menu.value]

            #Define the bbox with the selected values
            if (tab.selected_index==0):
                bbox = (lonmin.value, latmin.value, lonmax.value, latmax.value)
            else:
                 polygon, bbox = polygon_bbox_country(country_menu.value)
                    
            #Get the image
            img = cams_wms.getMapImage(wms, layer, bbox, (width_menu.value, height_menu.value), times_menu.value, elevations_menu.value)

            #Open the image
            legendGraphic = cams_wms.getLegend(layer)

            with out:
                plt.close()
                clear_output()
                cams_wms.plotMapLegend(img, legendGraphic, layer.name.replace('_', ' ') , bbox).show()

        button.on_click(click)

# ----------------------------------------------------------------
#  CAMS download web service class
# ----------------------------------------------------------------
class cams_download():
        
    def downloadPackage(token, model, method, pollutant, time, date, level):  
                
        leveltype = "ALLLEVELS"
        if level == 0:
            leveltype = "SURFACE"

        dlurl = dlserver + "&token=" + token + "&grid=0.1&model=" + model + "&package=" + method + "_" +  \
            pollutant + "_" + leveltype + "&time=" + time +"&referencetime=" + date + "T00:00:00Z&format=GRIB2"

        resp = requests.get(dlurl)
        
        data_name = model + '_' + method + '_' + pollutant + '_' + date + '_' + time + '_level_' + str(level)

        #Get the destination folder path
        dir = '/home/jovyan/work/cams_data/cams_europe_services/03_Download_packaged_data/' + \
            model + '_' + method + '_' + pollutant 
            
        #Create the folder if it doesn't exist
        if not os.path.exists(dir):
            os.makedirs(dir)

        filename = data_name + '.grib'

        #Create a file
        f = open(os.path.join(dir, filename),'wb')
        f.write(resp.content)
        f.close()


    def displayMap(token):
        
        times = { "FORECAST": ["0H24H", "25H48H", "49H72H", "73H96H"], "ANALYSIS": ["-24H-1H"]}

        methods_menu  = widgets.Dropdown(
            options=methods,
            value=methods[0],
            description='Method:',
            disabled=False,
        )

        models_menu = widgets.Dropdown(
            options=models,
            value=models[0],
            description='Model:',
            disabled=False,
        )
        
        pollutants = species
        if (methods_menu.value == 'ANALYSIS'):
            pollutants = [i for i in species if i not in pollens]

        species_menu = widgets.Dropdown(
            options=pollutants,
            value=pollutants[0],
            description='Species:',
            disabled=False,
        )

        times_menu = widgets.Dropdown(
            options=times[methods_menu.value],
            value=times[methods_menu.value][0],
            description='Times:',
            disabled=False,
        )
        
        available_levels = levels
        if species_menu.value in pollens:
            available_levels = [0]
    
        levels_menu = widgets.Dropdown(
            options=available_levels,
            value=available_levels[0],
            description='Level:',
            disabled=False,
        )

        def handle_methods_menu_change(change):
            pollutants = species
            if (change.new == 'ANALYSIS'):
                pollutants = [i for i in species if i not in pollens]
            species_menu.options=pollutants
            species_menu.value=pollutants[0]            
            times_menu.options=times[change.new]
            times_menu.value=times[change.new][0]

        def handle_species_menu_change(change):
            available_levels = levels
            if change.new in pollens:
                available_levels = [0]
            levels_menu.options=available_levels
            levels_menu.value=available_levels[0]

        methods_menu.observe(handle_methods_menu_change, names='value')
        species_menu.observe(handle_species_menu_change, names='value')
         
        from IPython.display import Image

        dates_menu = widgets.DatePicker(
            description='Date:',
            value = datetime.date.today() - timedelta(days=30),
            disabled=False
        )

        display(methods_menu, models_menu, species_menu, times_menu, dates_menu, levels_menu)
        
        tab, lonmin, latmin, lonmax, latmax, country_menu = geographical_area_tab()

        display(widgets.Label(value="Select a geographical area in Europe:"), tab)

        #Display the validate button
        out=widgets.Output()
        button=widgets.Button(description='Validate')
        vbox=widgets.VBox([button, out])
        display(vbox)

        def click(b):
            
            model = models_menu.value
            method = methods_menu.value
            pollutant = species_menu.value
            date = dates_menu.value.strftime("%Y-%m-%d")
            time = times_menu.value
            level = levels_menu.value

            cams_download.downloadPackage(token, model, method, pollutant, time, date, level)

            data_name = model + '_' + method + '_' + pollutant + '_' + date + '_' + time + '_level_' + str(level)

            #Define the bbox with the selected values
            if (tab.selected_index == 0):
                bbox = (lonmin.value, latmin.value, lonmax.value, latmax.value)
            else:
                 polygon, bbox = polygon_bbox_country(country_menu.value)
                    
            #Get the destination folder path
            dir = '/home/jovyan/work/cams_data/cams_europe_services/03_Download_packaged_data/' + \
                model + '_' + method + '_' + pollutant 

            #Open the GRIB file
            import pygrib
            grbs = pygrib.open(os.path.join(dir, data_name + '.grib'))

            with out:
                clear_output()
                
                if (grbs.messages==0):
                    leveltype = "ALLLEVELS"
                    if level == 0:
                        leveltype = "SURFACE"
                    print('No data available in the file')
                    return 0
                grb = grbs.select()[0]

                vmax = np.amax(grb.values)

                result_filename = data_name + "_result.gif"

                gribs = grbs.select(level=levels_menu.value)
                
                f = widgets.FloatProgress(min=0, max=len(gribs) - 1)
                label = widgets.Label(value="Downloading 0%")

                display(label, f)
                nb = 0
                
                #Create a new image for each time
                for grb in gribs:
                    time = grb['stepRange']
                    plt = plotGrib(grb, pollutant + ' ' + date + ' time: ' + time + ' level: ' + str(levels_menu.value), \
                                   0, vmax, bbox=bbox)
                    plt.savefig(os.path.join(dir, model + '_' + method + '_' + pollutant + '_nb_' + str(nb) + '.png'))
                    plt.close()
                    nb += 1
                    f.value += 1
                    label.value = 'Downloading ' + str(round(f.value/f.max*100)) + '%'

                #Create a GIF 
                import imageio 

                images = [ imageio.imread(os.path.join(dir,  model + '_' + method + '_' + \
                                                       pollutant + '_nb_' + str(i) + '.png')) for i in range(1, len(gribs))]
                imageio.mimsave(os.path.join(dir, result_filename), images, 'GIF', duration=0.2)
                
                clear_output()
                display(Image(os.path.join(dir, result_filename)))

        button.on_click(click)


# ------------------------------------------
# Cams pollution average
# ------------------------------------------

def avg_data_ecmwf(dir,filename) :
    gaz_dico = {"NO2":"125.210","CO":"127.210","SO2":"126.210"}

    first_date = widgets.DatePicker(value = datetime.date(2020, 1, 1), description='Start date :',disabled=False)
    second_date = widgets.DatePicker(value = datetime.date(2020, 1, 31), description='End date :',disabled=False)
    gaz = widgets.Dropdown(options=['NO2', 'CO', 'SO2'],value='NO2',description='Gaz :',disabled=False)
    button = widgets.Button(description = 'Validate')
    check_download = widgets.Checkbox(value=False,description='Download',disabled=False,indent=False)

    dl_menu = widgets.VBox([check_download,first_date,second_date,gaz,button])

    children = [dl_menu]

    global tab 
    tab = widgets.Tab()
    tab.children = children
    tab.set_title(0, 'Download')
    tab.set_title(1,'No Download')

    out = widgets.Output()
    display(tab)
    display(out)

    def click(b) :
        with out :

            clear_output(wait=True)

            if check_download.value :
                server = ECMWFDataServer()
                server.retrieve({
                    "class": "mc",
                    "dataset": "cams_nrealtime",
                    "date": first_date.value.strftime("%Y-%m-%d") + "/to/" + second_date.value.strftime("%Y-%m-%d"),
                    "expver": "0001",
                    "levtype": "sfc",
                    "param": gaz_dico[gaz.value],
                    "step": "0",
                    "stream": "oper",
                    "time": "00:00:00/06:00:00/12:00:00/18:00:00",
                    "type": "an",
                    "target": filename,
                })
                print("New data dowloaded")
            else :
                print("No new data dowloaded")
            

    
            #Select a place and a colormap
            lonmax = widgets.FloatText(value = 146, description = 'Long max:', disabled = False, step = 0.001)
            latmax = widgets.FloatText(value = 54, description = 'Lat max:', disabled = False, step = 0.001)
            lonmin = widgets.FloatText(value = 70, description = 'Long min:', disabled = False, step = 0.001)
            latmin = widgets.FloatText(value = 8, description = 'Lat min:', disabled = False, step = 0.001)
            button2 = widgets.Button(description = 'Validate')

            bbox_menu = widgets.VBox([lonmax, latmax, lonmin, latmin])

            raw_bbox_menu = widgets.Textarea(
                value='146,54,70,8',
                placeholder='BBOX',
                disabled=False,
                layout=widgets.Layout(width='50%')
            )

            children = [bbox_menu,
                        widgets.VBox([
                           widgets.Label(value="Enter a raw BBOX:"),
                           raw_bbox_menu
                       ])]

            global tab2
            tab2 = widgets.Tab()
            tab2.children = children
            tab2.set_title(0, 'Manual bbox')
            tab2.set_title(1, 'Raw bbox')
            out2 = widgets.Output()
            display(tab2)
            display(button2)
            display(out2)

            def change_data_longitude(value) :
                if value >= 180 :
                    return value - 360
                else :
                    return value

            mychange = np.vectorize(change_data_longitude)


            def click2(b) :
                with out2 :
                    
                    if (tab2.selected_index == 0):
                        bbox = [lonmax.value, latmax.value, lonmin.value, latmin.value]
                    elif (tab2.selected_index == 1):
                        bbox = tuple(map(float, raw_bbox_menu.value.split(',')))
                    else :
                        print('error')

                    clear_output(wait=True)
                    print('Bounding box recorded : ' + str(bbox[0]) + ',' + str(bbox[1]) + ',' + str(bbox[2]) + ',' + str(bbox[3]))

                    first_date2 = widgets.DatePicker(value = datetime.date(2020, 1, 1), description='Start avg :',disabled=False)
                    second_date2 = widgets.DatePicker(value = datetime.date(2020, 1, 31), description='End avg :',disabled=False)
                    vmax = widgets.FloatText(value = -1, description = 'vmax:', disabled = False, step = 0.001)
                    button2 = widgets.Button(description = 'Validate')

                    button3 = widgets.Button(description = 'Validate')
                    bbox_menu2 = widgets.VBox([first_date2,second_date2,vmax,button3])
                    children = [bbox_menu2]

                    global tab3 
                    tab3 = widgets.Tab()
                    tab3.children = children
                    tab3.set_title(0, 'Date and colormap')

                    out3 = widgets.Output()

                    display(tab3)
                    display(out3)

                    def click3(b):
                        with out3 :
                            
                            start = (first_date2.value-first_date.value).days
                            period = (second_date2.value-first_date2.value).days

                            # Open a GRIB file
                            grbs = pygrib.open(filename)

                            grb = grbs.select()[0]

                            # Get the longitudes and the latitudes 
                            latitudes,longitudes = grb.latlons()

                            #In EPSG:4326
                            lat_min = bbox[3]
                            lat_max = bbox[1]
                            long_min = bbox[2]
                            long_max = bbox[0]

                            unit = grb['units']

                            figure(num=None, figsize=(16, 10))

                            # Create a map
                            map = Basemap(projection='cyl', lat_ts=10, llcrnrlon=long_min,
                                        urcrnrlon=long_max,llcrnrlat=lat_min,urcrnrlat=lat_max,
                                        resolution='l')

                            map.drawcoastlines()

                            # Create and save a figure for each grib message

                            data = np.zeros(longitudes.shape)
                            nb_data = 0
                            longitudes = mychange(longitudes)

                            indice = 0
                            while longitudes[0][indice] >= 0 :
                                indice = indice + 1

                            long1 = longitudes[:,indice:longitudes[0].shape[0]]
                            long2 = longitudes[:,0:indice]

                            longitudes = np.concatenate((long1,long2),1)

                            clear_output(wait=True)
                            for i in tqdm(range(start*4, (start+period)*4)) :
                                
                                grb = grbs.select()[i]

                                data0 = grb.values
                                data1 = data0[:,indice:data0[0].shape[0]]
                                data2 = data0[:,0:indice]
                                data = data + np.concatenate((data1,data2),1)
                                nb_data = nb_data + 1


                            data = data/nb_data

                            # Display the data

                            if vmax.value == -1 :
                                lon_s = longitudes[0]
                                i_long_min = 0
                                while lon_s[i_long_min] <= long_min  :
                                    i_long_min = i_long_min + 1

                                i_long_max = i_long_min
                                while lon_s[i_long_max] <= long_max :
                                    i_long_max = i_long_max + 1

                                lat_s = latitudes[:,0]
                                i_lat_max = 0
                                while lat_s[i_lat_max] >= lat_max  :
                                    i_lat_max = i_lat_max + 1

                                i_lat_min = i_lat_max
                                while lat_s[i_lat_min] >= lat_min :
                                    i_lat_min = i_lat_min + 1

                                max_value = np.max(data[i_lat_max:i_lat_min,i_long_min:i_long_max])
                            else :
                                max_value = vmax.value



                            cs = map.pcolormesh(longitudes, latitudes, data, cmap=plt.cm.jet, vmin=0, vmax=max_value)
                            map.colorbar(cs, label=unit)

                            plt.title(gaz.value + ' date: ' + first_date2.value.strftime("%Y-%m-%d") + " to " + second_date2.value.strftime("%Y-%m-%d") + ' type : ' + ' average ')
                            plt.savefig(os.path.join(dir + 'result_avg'))
                            plt.close()
                            display(Image(path.join(dir, 'result_avg.png')))

                    button3.on_click(click3)

            button2.on_click(click2)

    button.on_click(click)
    
    return

    