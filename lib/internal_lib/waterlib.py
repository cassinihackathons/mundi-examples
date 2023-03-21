# Library containing all the useful functions for the GIF_Generation Notebook
# Author : Lenoir d'Espinasse Guillaume
# Contact email : guillaume.lenoirdespinasse@atos.net

import datetime
import glob
import imageio
import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np
import os
import urllib
import folium
import requests
import xml.etree.ElementTree as ET
from ast import literal_eval as make_tuple
from io import BytesIO

from IPython.display import clear_output, HTML, FileLink, FileLinks, display
from mundilib import MundiCatalogue
from PIL import Image, ImageDraw, ImageFont, ImageOps
from utils import city_polygon_bbox

# --------------------------
#  Global Variables
# --------------------------

# TODO : Add new collections when available
COLLECTION_OPTIONS = [('Sentinel2-L1C', ('Sentinel2', 'L1C')), ('Sentinel2-L2A', ('Sentinel2', 'L2A')),
                      ('Sentinel1-GRD', ('Sentinel1', 'GRD')), ('Sentinel5P-L2', ('Sentinel5P', 'L2'))]

# Starting date of each satellite
# TODO : Add new satellites when available
DATE_DICT = {
    'Sentinel1': datetime.date(2018, 9, 1),
    'Sentinel2': datetime.date(2016, 10, 15),
    'Sentinel5P': datetime.date(2018, 9, 1)
}

# Logos URL
URL_LOGO_WHITE = 'https://mundiwebservices.com/build/assets/Mundi-Logo-CMYK-white.png'
URL_LOGO_COLORS = 'https://mundiwebservices.com/build/assets/Mundi-Logo-CMYK-colors.png'

# Path to the Mundi Font
TTF_PATH = "/home/jovyan/lib/dependencies/fonts/poppins-light.ttf"

SAVE_FOLDER = "/home/jovyan/work/water_detection/"
SAVE_FOLDER_IMAGES = f"{SAVE_FOLDER}images/"
SAVE_FOLDER_GIF = f"{SAVE_FOLDER}gif/"

dates_list = []
bbox_to_save = []


class BboxTooLarge(Exception):
    pass


# --------------------------
#  Useful functions
# --------------------------

def setup():
    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)


def get_image(bbox, wms_layers, time):
    """This function makes the WMS request to MundiCatalogue to download the chosen image

    Parameters
    ----------
    bbox: numpy.array
        The BBOX of the area chosen
    height: int
        The height (in pixels) of the returned image
    width: int
        The width (in pixels) of the returned image
    wms_layers: int
        # of layer to extract
    time: string
        Period of time to select the image
    satellite: string
        Satellite chosen
    collection: string
        Collection chosen

    Returns
    -------
    img:
        Link to the image to download/open
    """

    time_temp = time.split('/')
    start_date = time_temp[0]
    stop_date = time_temp[1]

    xmin = bbox[2]
    ymin = bbox[3]
    xmax = bbox[0]
    ymax = bbox[1]

    url = 'http://shservices.mundiwebservices.com/ogc/wms/ea23bfb3-2a67-476f-90e3-fe54873ff897?SERVICE=WMS&REQUEST=GetMap&TRANSPARENT=true&LAYERS=SCL-WATER-ONLY&VERSION=1.1.1&FORMAT=image%2Fpng&STYLES=&showLogo=false&time=' + str(
        start_date) + '%2F' + str(stop_date) + '&RESX=10m&RESY=10m&SRS=EPSG%3A4326&BBOX=' + str(xmin) + '%2C' + str(
        ymin) + '%2C' + str(xmax) + '%2C' + str(ymax)

    img = requests.get(url)

    if img.status_code == 400:
        raise BboxTooLarge()

    black_pixel, total_pixel = pixel_analysis(BytesIO(img.content), (0, 0, 0))

    if black_pixel / total_pixel > 0.95:
        raise BboxTooLarge()

    files = glob.glob(f'{SAVE_FOLDER_IMAGES}*')
    f = open(r'/home/jovyan/work/water_detection/images/' + str(len(files)) + '.png', 'wb')
    f.write(img.content)
    f.close()


def get_date(bbox, wms_layers, time, width, height):
    """This function makes the WMS request to MundiCatalogue to get the date of the image requested

    Parameters
    ----------
    bbox: numpy.array
        The BBOX of the area chosen
    height: int
        The height (in pixels) of the returned image
    width: int
        The width (in pixels) of the returned image
    wms_layers: int
        # of layer to extract
    time: string (YYYY-MM-DD)
        Period of time to select the image
    satellite: string
        Satellite chosen
    collection: string
        Collection chosen

    Returns
    -------
    date:
        Acquisition date of the image downloaded
    """
    date = 'YYYY-MM-DD'
    c = MundiCatalogue()
    wms = c.get_collection('Sentinel2').mundi_wms('L2A')

    projection = 'EPSG:4326'

    layers = list(wms.contents)

    for layer in layers:
        if wms_layers == layer:
            index_layer = layers.index(layer)

    response = wms.getfeatureinfo(layers=[wms[layers[index_layer]].name],
                                  srs=projection,
                                  bbox=bbox,
                                  size=(width, height),
                                  info_format='text/xml',
                                  time=time,
                                  showlogo=False,
                                  xy=(width // 2, height // 2)
                                  )

    root = ET.fromstring(response.read())
    for child in root:
        date = child.attrib['date']

    return date


def add_logo(image, logo_white, border=True):
    """This function pastes a logo on an image

    Parameters
    ----------
    image: PIL.PngImagePlugin.PngImageFile
        The original image onto which you want to add a logo
    logo_white: PIL.PngImagePlugin.PngImageFile
        The logo you want to add to your image
    border: bool
        Whether to add a border ot the logo
    """

    # Resize Logo white
    wsize = int(image.size[1] * 0.30)
    wpercent = (wsize / float(logo_white.size[0]))
    hsize = int((float(logo_white.size[1]) * float(wpercent)))

    simage = logo_white.resize((wsize, hsize))

    if border:
        # Changing the logo color to white
        logo_black = ImageOps.colorize(simage.convert('L'), black="blue", white="black")

        # Adding black border to the image
        border_size = 1
        box1 = (int(0.08 * image.size[1]) - border_size, int(0.035 * image.size[0]) - border_size)
        image.paste(logo_black, box1, simage)
        box2 = (int(0.08 * image.size[1]) + border_size, int(0.035 * image.size[0]) - border_size)
        image.paste(logo_black, box2, simage)
        box3 = (int(0.08 * image.size[1]) - border_size, int(0.035 * image.size[0]) + border_size)
        image.paste(logo_black, box3, simage)
        box4 = (int(0.08 * image.size[1]) + border_size, int(0.035 * image.size[0]) + border_size)
        image.paste(logo_black, box4, simage)

    # Left top corner
    box = (int(0.08 * image.size[1]), int(0.035 * image.size[0]))
    image.paste(simage, box, simage)


def download_images(bbox, layer, start_date, stop_date,
                    title, subtitle, delta_days):
    """This functions generates the GIF file with the given parameters

    Parameters
    ----------
    bbox: numpy.array
        The BBOX of the area chosen
    collection: tuple
        tuple containing the satellite and the collection
    layer: int
        # of layer to create the GIF
    start_date : datetime.datetime
        The start date of your GIF
    stop_date : datetime.datetime
        The stop date of your GIF
    title: string
        The title you want to print on your GIF
    subtitle: string
        The subtitle you want to print on your GIF
    delta_days: int
        number of days between two img
    height: int
        The height (in pixels) of the returned image
    width: int
        The width (in pixels) of the returned image
    """

    # Emptying the folder with img
    if not os.path.exists(SAVE_FOLDER_IMAGES):
        os.makedirs(SAVE_FOLDER_IMAGES)
    number_image = 0
    files = glob.glob(f'{SAVE_FOLDER_IMAGES}*')
    for f in files:
        os.remove(f)
        number_image = len(files) - 1

        # Emptying dates_list
    dates_list.clear()

    current_date = start_date

    # Importing Mundi_logo
    logo_white = Image.open(urllib.request.urlopen(URL_LOGO_WHITE))
    logo_white.mode = 'RGBA'

    clear_output(wait=True)
    k = str(int((stop_date - current_date).days / delta_days))
    cpt = 0
    images = []

    while current_date < stop_date:

        next_date = current_date + datetime.timedelta(delta_days, 0)
        time = current_date.strftime("%Y-%m-%d") + '/' + next_date.strftime("%Y-%m-%d")
        print("\r Image #" + str(cpt) + "/" + k + " : " + time)
        try:
            get_image(bbox, layer, time)
        except BboxTooLarge:
            print("The bounding box is too large, please redefine it with www.bboxfinder.com")
            return

        files = glob.glob(f'{SAVE_FOLDER_IMAGES}*')

        number_image = len(files) - 1
        image = Image.open('/home/jovyan/work/water_detection/images/' + str(number_image) + '.png')
        width, height = image.size
        image = image.convert('RGB')
        # Choosing fonts for the date, title and subtitle
        # The characters are written in white with a black thin border
        border = 1
        fnt = ImageFont.truetype(TTF_PATH, int(width / 45))
        fnt2 = ImageFont.truetype(TTF_PATH, int(width / 30))
        fnt3 = ImageFont.truetype(TTF_PATH, int(width / 55))
        draw = ImageDraw.Draw(image)
        date = get_date(bbox, layer, time, width, height)
        dates_list.append(date)

        # Drawing the texts on the image
        # The date
        draw.text((0.82 * width - border, 0.10 * height - border), date, (0, 0, 0), fnt)
        draw.text((0.82 * width + border, 0.10 * height - border), date, (0, 0, 0), fnt)
        draw.text((0.82 * width - border, 0.10 * height + border), date, (0, 0, 0), fnt)
        draw.text((0.82 * width + border, 0.10 * height + border), date, (0, 0, 0), fnt)
        draw.text((0.82 * width, 0.10 * height), date, (255, 255, 255), fnt)
        # The title
        draw.text((0.05 * width - border, 0.85 * height - border), title, (0, 0, 0), fnt2)
        draw.text((0.05 * width + border, 0.85 * height - border), title, (0, 0, 0), fnt2)
        draw.text((0.05 * width - border, 0.85 * height + border), title, (0, 0, 0), fnt2)
        draw.text((0.05 * width + border, 0.85 * height + border), title, (0, 0, 0), fnt2)
        draw.text((0.05 * width, 0.85 * height), title, (255, 255, 255), fnt2)
        # The subtitle
        draw.text((0.05 * width - border, 0.93 * height - border), subtitle, (0, 0, 0), fnt3)
        draw.text((0.05 * width + border, 0.93 * height - border), subtitle, (0, 0, 0), fnt3)
        draw.text((0.05 * width - border, 0.93 * height + border), subtitle, (0, 0, 0), fnt3)
        draw.text((0.05 * width + border, 0.93 * height + border), subtitle, (0, 0, 0), fnt3)
        draw.text((0.05 * width, 0.93 * height), subtitle, (255, 255, 255), fnt3)
        # Adding the logo
        add_logo(image, logo_white)

        images.append(np.array(image))
        filename = str(cpt) + '.png'
        image.save(SAVE_FOLDER_IMAGES + filename)
        current_date = next_date
        cpt += 1
        clear_output(wait=True)

    print("All img downloaded on time !")


def generate_gif_from_folder(duration, output_name, end_gif_duration, folder=SAVE_FOLDER_IMAGES, logo_url=None,
                             sort_key=lambda y: int(y.split(".")[0]), accepted_extensions=None, display_texts=None,
                             display_text_font_size=lambda img: int(img.width / 20)):
    f"""This functions generates the GIF file from the files in your /work/gif_images

    Parameters
    ----------
    duration: int
        The duration (in seconds) of the GIF
    output_name: string
        The name of your GIF file
    end_gif_duration: int
        The last image of the GIF will be repeated this number of times
    folder: str
        Path to the folder in which the img are. The img filenames must be an incremented integer: the output GIF
        consists of the img sorted by filename. Defaults to "{SAVE_FOLDER_IMAGES}"
    logo_url: str
        An URL leading to a logo to add on the upper left corner of the img. If None, no logo is added (default)
    sort_key: callable
        Function used to sort the img ("key" option to "sorted" function). By default, it's assumed that filenames 
        are "<integer>.png" and they are sorted them in ascending order 
    accepted_extensions: list
        List of filename extensions of the img to consider. Files with other extensions are ignored. Defaults to 
        ["png"] 
    display_texts: list
        List of names to overlay on each image. The size must be the same as the number of img retrieved. If None, no
        name is overlaid
    display_text_font_size: int or callable
        An integer or a formula taking a PIL Image class as argument to compute the font size of the text to display. Ignored if 
        display_texts is None
    """
    if not os.path.exists(SAVE_FOLDER_GIF):
        os.makedirs(SAVE_FOLDER_GIF)
    images = []
    if accepted_extensions is None:
        accepted_extensions = ["png"]

    # get filenames sorted in integer order (strings are not sorted as integers)
    filenames = [fn for fn in os.listdir(folder) if fn.split(".")[-1] in accepted_extensions]
    final_filenames = sorted(filenames, key=sort_key)

    # fill displays_texts with empty strings if not specified
    if display_texts is None:
        display_texts = [None] * len(final_filenames)

    # check that sizes of final_filenames & display_texts match
    if len(final_filenames) != len(display_texts):
        raise ValueError(
            f"display_texts' length must be the number of img ({len(display_texts)} vs {len(final_filenames)})")

    # download Mundi logo
    logo_img = None
    if logo_url is not None:
        logo_img = Image.open(urllib.request.urlopen(logo_url))
        logo_img.mode = 'RGBA'

    k = len(final_filenames)
    if display_texts is not None and len(display_texts) != k:
        raise ValueError(
            f"size of 'display_names' is not equal to the number of files found ({len(display_texts)} vs {k}")

    # open all img
    for cpt, (file, display_text) in enumerate(zip(final_filenames, display_texts)):
        print(f"\r Image #{cpt}/{k}")
        image = Image.open(os.path.join(folder, file)).convert("RGB")

        # add Mundi logo
        if logo_url is not None:
            add_logo(image, logo_img, border=False)

        # add filename
        if display_text is not None:
            if isinstance(display_text_font_size, int) or isinstance(display_text, float):
                font_size = display_text_font_size
            else:
                font_size = display_text_font_size(image)
            font = ImageFont.truetype(TTF_PATH, font_size)

            draw = ImageDraw.Draw(image)
            draw.text((image.width * .08, image.height * .88), display_text, (0, 0, 0), font)

        images.append(np.array(image))
        clear_output(wait=True)

    # Repeating the last image x times to have a stop at the end of the GIF
    last_image = images[-1]
    for i in range(end_gif_duration):
        images.append(np.array(last_image))

    imageio.mimsave(os.path.join(SAVE_FOLDER_GIF, output_name), images, duration=duration / int(k))
    clear_output(wait=True)
    print("GIF File Generated")


# --------------------------
#  Display functions
# --------------------------


# Main function
# By calling this function, widgets will be displayed and each time the user
# clicks on validate, a new function will be called and new widgets will be
# displayed.


def get_bbox(tab, out, lonmax, latmax, lonmin, latmin, cities_menu, raw_bbox_menu):
    """This function validates the bbox and display it to the user

    Parameters
    ----------
    tab: ipywidgets.Tab()
        Tab widget for selection between BBOX and cities
    out: ipywidgets.Output()
        Output widget to display the BBOX to the user
    lonmax,latmax,lonmin,latmin: ipywidgets.FloatText()
        Widgets containing the values of the BBOX entered by user
    cities_menu: ipywidgets.Text()
        Widget containing the city selected by user

    Returns
    -------
    bbox: tuple
        The bounding box chosen by user
    """
    if (tab.selected_index == 2):
        polygon, bbox, place_name = city_polygon_bbox(cities_menu.value)
        with out:
            print(place_name)
    elif (tab.selected_index == 1):
        bbox = [lonmax.value, latmax.value, lonmin.value, latmin.value]
    elif (tab.selected_index == 0):
        bbox = tuple(map(float, raw_bbox_menu.value.split(',')))
    lonmax.value = bbox[0]
    latmax.value = bbox[1]
    lonmin.value = bbox[2]
    latmin.value = bbox[3]
    raw_bbox_menu.value = ','.join([str(elem) for elem in bbox])
    with out:
        print(f'BBOX = ({raw_bbox_menu.value})')
        clear_output(wait=True)
    return bbox


def get_images():
    """This function allows to define the image parameters
    """

    bbox_to_display = str(bbox_to_save).replace('[', '').replace(']', '')
    bbox = make_tuple(bbox_to_display)

    start_date_widget = widgets.DatePicker(
        description='Starting Date',
        value=datetime.date.today() - datetime.timedelta(55),
        disabled=False
    )
    stop_date_widget = widgets.DatePicker(
        description='Stopping Date',
        value=datetime.date.today() - datetime.timedelta(14),
        disabled=False
    )
    title_widget = widgets.Text(
        value='',
        placeholder='Title to print on the GIF',
        description='Title',
        disabled=False
    )
    subtitle_widget = widgets.Text(
        value='',
        placeholder='Subtitle to print on the GIF',
        description='Subtitle',
        disabled=False
    )
    delta_days_widget = widgets.IntText(
        value=30,
        description='Time frame to acquire data',
        disabled=False
    )
    button_widget = widgets.Button(
        description='Download img',
        disabled=False,
        button_style='',
        tooltip='Click me',
    )
    output_widget = widgets.Output(
    )
    output_gif = widgets.Output(
    )

    display(start_date_widget)
    display(stop_date_widget)
    display(title_widget)
    display(subtitle_widget)
    display(delta_days_widget)
    display(button_widget)
    display(output_widget)
    display(output_gif)

    def click_gif(b):
        with output_widget:
            download_images(bbox, 'SCL-WATER-ONLY', start_date_widget.value,
                            stop_date_widget.value, title_widget.value, subtitle_widget.value,
                            delta_days_widget.value)

    button_widget.on_click(click_gif)


def gif_creation():
    """This function creates a GIF file based on images stored in the /work/water_detection/images/ folder
    """

    accepted_extensions = ["png"]
    filenames = [fn for fn in os.listdir(SAVE_FOLDER_IMAGES) if fn.split(".")[-1] in accepted_extensions]
    temp = [int(fn.split('.')[0]) for fn in filenames]
    temp = sorted(temp)
    final_filenames = [f'{elt}.png' for elt in temp]
    length_filenames = len(final_filenames)
    length_dates_list = len(dates_list)
    plt.figure(figsize=(25, 20))
    columns = 5
    i = 0

    for file in final_filenames:
        plt.subplot(length_filenames / columns + 1, columns, i + 1)
        plt.title(file)
        i += 1
        plt.imshow(Image.open(f"{SAVE_FOLDER_IMAGES}{file}"))

    file_widget = widgets.Dropdown(
        options=final_filenames,
        description='File To Delete',
    )
    button_del = widgets.Button(description='Delete this file')
    out_wid_del = widgets.Output()

    duration_widget = widgets.IntText(
        value=5,
        description='GIF Duration (in seconds)',
        disabled=False
    )
    end_gif_duration_widget = widgets.IntText(
        value=3,
        description='End GIF Duration (last image rep times)',
        disabled=False
    )
    output_name_widget = widgets.Text(
        value='output.gif',
        placeholder='Output Name',
        description='Output Name',
        disabled=False
    )
    button_widget = widgets.Button(
        description='Generate GIF',
        disabled=False,
        button_style='',
        tooltip='Click me',
    )
    out_wid_create = widgets.Output()

    box_layout = widgets.Layout(
        border='',
        margin='0px 20px 20px 0px',
        padding='5px 60px 5px 60px')

    vbox1 = widgets.VBox([widgets.Label('Delete some img'), file_widget, button_del, out_wid_del])
    vbox1.layout = box_layout
    vbox2 = widgets.VBox(
        [widgets.Label('Generate the GIF'), duration_widget, end_gif_duration_widget, output_name_widget, button_widget,
         out_wid_create])
    vbox2.layout = box_layout

    display(widgets.HBox([vbox1, vbox2]))

    def click_file(b):
        with out_wid_del:
            clear_output(wait=True)
            index_in_date_list = final_filenames.index(file_widget.value)
            os.remove(f'{SAVE_FOLDER_IMAGES}{file_widget.value}')
            del dates_list[index_in_date_list]
            print(f'File {file_widget.value} deleted')

    def click_generate(b):
        with out_wid_create:
            generate_gif_from_folder(duration_widget.value, output_name_widget.value, end_gif_duration_widget.value)

    button_del.on_click(click_file)
    button_widget.on_click(click_generate)


# -------------------------------------------
#  Water Permanent detection notebook functions :
# -------------------------------------------


def define_parameters_first_map():
    """This function allows the user to define paremeters needed to create the folium map"""

    lonmax = widgets.FloatText(value=-0.191231, description='Long max:', disabled=False, step=0.001)
    latmax = widgets.FloatText(value=51.472096, description='Lat max:', disabled=False, step=0.001)
    lonmin = widgets.FloatText(value=-0.004120, description='Long min:', disabled=False, step=0.001)
    latmin = widgets.FloatText(value=51.560383, description='Lat min:', disabled=False, step=0.001)

    raw_bbox_menu = widgets.Textarea(
        value='-0.191231,51.472096,-0.004120,51.560383',
        placeholder='BBOX',
        disabled=False,
        layout=widgets.Layout(width='50%')
    )

    bbox_menu = widgets.VBox([
        widgets.Label(value="Enter a raw BBOX:"),
        raw_bbox_menu
    ])

    cities_menu = widgets.Text(placeholder='Ex: Toulouse, Paris, New-York...')

    children = [bbox_menu,
                widgets.VBox([lonmax, latmax, lonmin, latmin]),
                widgets.VBox([
                    widgets.Label(value="Enter a city:"),
                    cities_menu
                ]),
                ]

    tab = widgets.Tab()
    tab.children = children
    tab.set_title(0, 'Raw Bounding Box')
    tab.set_title(1, 'Bounding Box')
    tab.set_title(2, 'Cities')

    start_date_widget = widgets.DatePicker(
        description='Starting Date',
        value=datetime.date.today() - datetime.timedelta(45),
        disabled=False
    )
    stop_date_widget = widgets.DatePicker(
        description='Stopping Date',
        value=datetime.date.today() - datetime.timedelta(14),
        disabled=False
    )

    global_output = widgets.Output()
    out = widgets.Output()
    button = widgets.Button(description='Validate')

    display(tab)
    display(start_date_widget)
    display(stop_date_widget)
    display(button)
    display(out)
    display(global_output)

    bbox = [1.5153795, 43.668708, 1.3503956, 43.532654]  # default bbox on Toulouse

    # Defines the action when the button is clicked.
    # Here the button validates the bbox, and call the next widget (collection_widget)
    def click_bbox(b):
        global bbox
        bbox = get_bbox(tab, out, lonmax, latmax, lonmin, latmin, cities_menu, raw_bbox_menu)

        with global_output:
            print(bbox)
            clear_output(wait=True)
            map = create_folium_map(bbox, start_date_widget.value, stop_date_widget.value)
            folium.TileLayer(opacity=0.3).add_to(map)
            display(HTML('<h3>Water permanent detection map between ' + str(start_date_widget.value) + ' and ' + str(
                stop_date_widget.value) + '</h1>'))
            display(map)

    button.on_click(click_bbox)


def create_folium_map(bbox, start_date, stop_date):
    """This function creates the folium map based on parameters defined in define_parameters_first_map function"""

    bbox_to_save.clear()
    bbox_to_save.append(bbox)

    xmin = bbox[2]
    ymin = bbox[3]
    xmax = bbox[0]
    ymax = bbox[1]
    centerx = (xmax + xmin) / 2
    centery = (ymax + ymin) / 2

    map = folium.Map(location=[centery, centerx], zoom_start=13, tiles='OpenStreetMap', max_native_zoom=19,
                     max_zoom=100)
    map.add_child(folium.raster_layers.WmsTileLayer(
        url='http://shservices.mundiwebservices.com/ogc/wms/ea23bfb3-2a67-476f-90e3-fe54873ff897?time=' + str(
            start_date) + '%2F' + str(stop_date) + '&RESX=10m&RESY=10m',
        layers=['SCL-WATER-ONLY'],
        fmt='image/png',
        version='1.3.0',
        attr='Sentinel2-L2A-SCL-layer',
        name='SCL',
        min_zoom=10,
        max_zoom=20
    ))

    return map


def define_parameters_second_map():
    """This function allows the user to define paremeters (time delta) needed to create the second folium map used to compare with the first map"""

    start_date_widget = widgets.DatePicker(
        description='Starting Date',
        value=datetime.date.today() - datetime.timedelta(45),
        disabled=False
    )
    stop_date_widget = widgets.DatePicker(
        description='Stopping Date',
        value=datetime.date.today() - datetime.timedelta(14),
        disabled=False
    )

    global_output = widgets.Output()
    out = widgets.Output()
    button = widgets.Button(description='Validate')

    display(start_date_widget)
    display(stop_date_widget)
    display(button)
    display(out)
    display(global_output)

    bbox = [1.5153795, 43.668708, 1.3503956, 43.532654]  # default bbox on Toulouse

    # Defines the action when the button is clicked.
    # Here the button validates the bbox, and call the next widget (collection_widget)
    def click_bbox(b):
        with global_output:
            clear_output(wait=True)
            map = create_2nd_folium_map(start_date_widget.value, stop_date_widget.value)
            folium.TileLayer(opacity=0.3).add_to(map)
            display(HTML('<h3>Water permanent detection map between ' + str(start_date_widget.value) + ' and ' + str(
                stop_date_widget.value) + '</h1>'))
            display(map)

    button.on_click(click_bbox)


def create_2nd_folium_map(start_date, stop_date):
    """This function creates the second folium map based on parameters defined in define_parameters_second_map function"""

    bbox_to_display = str(bbox_to_save).replace('[', '').replace(']', '')
    bbox = make_tuple(bbox_to_display)

    xmin = bbox[2]
    ymin = bbox[3]
    xmax = bbox[0]
    ymax = bbox[1]
    centerx = (xmax + xmin) / 2
    centery = (ymax + ymin) / 2

    map = folium.Map(location=[centery, centerx], zoom_start=13, tiles='OpenStreetMap', max_native_zoom=19,
                     max_zoom=100)
    map.add_child(folium.raster_layers.WmsTileLayer(
        url='http://shservices.mundiwebservices.com/ogc/wms/ea23bfb3-2a67-476f-90e3-fe54873ff897?time=' + str(
            start_date) + '%2F' + str(stop_date) + '&RESX=10m&RESY=10m',
        layers=['SCL-WATER-ONLY'],
        fmt='image/png',
        version='1.3.0',
        attr='Sentinel2-L2A-SCL-layer',
        name='SCL',
        min_zoom=10,
        max_zoom=20
    ))

    return map


def display_pixels():
    """This function calculates water surface area data on each image stored in the work/water_detection/images directory and display it in text and in graph bar"""

    accepted_extensions = ["png"]
    filenames = [fn for fn in os.listdir(SAVE_FOLDER_IMAGES) if fn.split(".")[-1] in accepted_extensions]
    list_histo = []
    total_blue = 0
    total_water_proportion = 0
    cpt = 0
    # get filenames sorted in integer order (strings are not sorted as integers)
    final_filenames = sorted(filenames, key=lambda y: int(y.split(".")[0]))

    for file in final_filenames:
        blue_pixel, total_pixel = pixel_analysis(SAVE_FOLDER_IMAGES + file, (0, 0, 255))
        blue_pixel_in_km2 = round((blue_pixel / 10000), 2)
        list_histo.append(np.array(blue_pixel_in_km2))

        total_blue = total_blue + blue_pixel_in_km2
        avg_km2 = round((total_blue / len(list_histo)), 2)

        water_proportion = round(((blue_pixel / total_pixel) * 100), 2)
        total_water_proportion = total_water_proportion + water_proportion
        avg_water_proportion = round((total_water_proportion / len(list_histo)), 2)
        print(str(total_pixel) + ' ' + str(blue_pixel))
        print('Image name : \033[1m' + str(file) + '\033[0m, Date : \033[1m' + dates_list[cpt] + '\033[0m :')
        print('The water surface area is : \033[1m\033[94m' + str(
            blue_pixel_in_km2) + 'km²\033[0m. The water proportion is : \033[1m\033[94m' + str(
            water_proportion) + '%\033[0m')
        cpt += 1

    display(HTML('<h3> The average water surface area is : <b>' + str(
        avg_km2) + 'km²</b>, and the average water proportion is : <b>' + str(avg_water_proportion) + '%</b>. </h3>'))
    print('')

    fig, ax = plt.subplots(figsize=(20, 10))
    ax.bar(dates_list, list_histo)
    ax.set_ylabel('water surface area (km²)')
    ax.set_xlabel('image date')
    ax.set_title(
        'Water permanent detection surface area (km²) evolution between ' + dates_list[0] + ' and ' + dates_list[-1])

    plt.show()


def pixel_analysis(path, value):
    im = Image.open(path)
    blue_pixel = 0
    total_pixel = 0
    nb_channels = len(value)
    for pixel in im.getdata():
        total_pixel += 1
        if pixel[:nb_channels] == value:  # if your image is RGB (if RGBA, (0, 0, 0, 255) or so
            blue_pixel += 1

    return blue_pixel, total_pixel
