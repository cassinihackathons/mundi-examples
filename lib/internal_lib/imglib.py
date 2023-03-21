# Library containing all the useful functions for the Easy Search Sentinel Image Notebook
# Author : ALCOUFFE Rémy / Lenoir d'Espinasse  Guillaume 
# Contact email : guillaume.lenoirdespinasse@atos.net

import datetime
import ipywidgets as widgets
import matplotlib.pyplot as plt
import os
import urllib
import xml.etree.ElementTree as ET
 
from IPython.display import clear_output, HTML, display
from mundilib import MundiCatalogue
from PIL import Image, ImageDraw, ImageFont, ImageOps
from utils import city_polygon_bbox



# --------------------------
#  Global Variables
# --------------------------

# TODO : Add new collections when available
COLLECTION_OPTIONS = [('Sentinel2-L1C', ('Sentinel2', 'L1C')), ('Sentinel2-L2A', ('Sentinel2', 'L2A'))]

# Starting date of each satellite
# TODO : Add new satellites when available
DATE_DICT = {
    'Sentinel1': datetime.date(2018, 9, 1),
    'Sentinel2': datetime.date(2016, 10, 15),
    'Sentinel5P': datetime.date(2018, 9, 1)
}

# Path to the Mundi Font
TTF_PATH = "/home/jovyan/lib/dependencies/fonts/poppins-light.ttf"

# Path to the save folder
SAVE_FOLDER_IMAGES = "/home/jovyan/work/sentinel2_images/"


# --------------------------
#  Useful functions
# --------------------------
def setup():
    """This function creates the SAVE_FOLDER_IMAGES if it has not been already created"""

    if not os.path.exists(SAVE_FOLDER_IMAGES):
        os.makedirs(SAVE_FOLDER_IMAGES)


def get_image(bbox, height, width, wms_layers, time, satellite, collection):
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
    sattellite: string
        Sattellite chosen
    collection: string
        Collection chosen
    
    Returns
    -------
    img:
        Link to the image to download/open
    """
    c = MundiCatalogue()
    wms = c.get_collection(satellite).mundi_wms(collection)
     
    projection = 'EPSG:4326'

    layers = list(wms.contents)
    
    for layer in layers:
        if wms_layers == layer:
            index_layer = layers.index(layer)

    img = wms.getmap(layers=[wms[layers[index_layer]].name],
                     srs=projection,
                     bbox=bbox,
                     size=(width, height),
                     format='image/png',
                     time=time,
                     showlogo=False,
                     transparent=False,
                     )
    return img


def get_date(bbox, height, width, wms_layers, time, sattellite, collection):
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
    sattellite: string
        Sattellite chosen
    collection: string
        Collection chosen
    
    Returns
    -------
    date:
        Acquisition date of the image downloaded
    """
    date = 'YYYY-MM-DD'
    c = MundiCatalogue()
    wms = c.get_collection(sattellite).mundi_wms(collection)

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


def add_logo(image, logo_white):
    """This function pastes a logo on an image

    Parameters
    ----------
    image: PIL.PngImagePlugin.PngImageFile
        The original image onto which you want to add a logo
    logo: PIL.PngImagePlugin.PngImageFile
        The logo you want to add to your image

    """

    # Resize Logo white
    wsize = int(image.size[1] * 0.30)
    wpercent = (wsize / float(logo_white.size[0]))
    hsize = int((float(logo_white.size[1]) * float(wpercent)))

    simage = logo_white.resize((wsize, hsize))

    # Changing the logo color to white
    logo_black = ImageOps.colorize(simage.convert('L'), black="blue", white="black")

    # Adding black border to the image
    border = 1
    box1 = (int(0.08 * image.size[1]) - border, int(0.035 * image.size[0]) - border)
    image.paste(logo_black, box1, simage)
    box2 = (int(0.08 * image.size[1]) + border, int(0.035 * image.size[0]) - border)
    image.paste(logo_black, box2, simage)
    box3 = (int(0.08 * image.size[1]) - border, int(0.035 * image.size[0]) + border)
    image.paste(logo_black, box3, simage)
    box4 = (int(0.08 * image.size[1]) + border, int(0.035 * image.size[0]) + border)
    image.paste(logo_black, box4, simage)

    # Left top corner
    box = (int(0.08 * image.size[1]), int(0.035 * image.size[0]))
    image.paste(simage, box, simage)


def download_images(bbox, collection, layer, start_date, stop_date,
                    title, file_name, height, width):
    """This functions generates the image file with the given parameters

    Parameters
    ----------
    bbox: numpy.array
        The BBOX of the area chosen
    collection: tuple
        tuple containing the sattellite and the collection
    layer: int
        # of layer to create the image
    start_date : string
        The start date of your image search
    stop_date : string
        The stop date of your image search
    download: boolean
        Boolean to chose either if you want to download the img or not
    title: string
        The title you want to print on your image
    file name: string
        The file name you want to give to your image
    height: int
        The height (in pixels) of the returned image
    width: int
        The width (in pixels) of the returned image
    """
    setup()

    (sattellite, collection) = collection

    # Importing Mundi_logo
    logo_white = Image.open(
        urllib.request.urlopen('https://mundiwebservices.com/build/assets/Mundi-Logo-CMYK-white.png'))
    logo_white.mode = ('RGBA')

    clear_output(wait=True)
    time = start_date.strftime("%Y-%m-%d") + '/' + stop_date.strftime("%Y-%m-%d")
    img = get_image(bbox, height, width, layer, time, sattellite, collection)
    image = Image.open(img)
    image = image.convert('RGB')

    # Choosing fonts for the date, title and subtitle
    # The characters are written in white with a black thin border
    border = 1
    fnt = ImageFont.truetype(TTF_PATH, int(width / 45))
    fnt2 = ImageFont.truetype(TTF_PATH, int(width / 30))
    fnt3 = ImageFont.truetype(TTF_PATH, int(width / 55))
    draw = ImageDraw.Draw(image)
    date = get_date(bbox, height, width, layer, time, sattellite, collection)
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
    # Adding the logo
    add_logo(image, logo_white)

    filename = file_name + '.png'
    image.save(SAVE_FOLDER_IMAGES + filename)

    clear_output(wait=True)
    print("Your image has been successfully downloaded and saved in the sentinel2_images folder !")
    print("")
    display(HTML('<img src="{}">'.format('../../work/sentinel2_images/' + file_name + '.png')))


# --------------------------
#  Display functions
# --------------------------

# Main function
# By calling this function, widgets will be displayed and each time the user
# clicks on validate, a new function will be called and new widgets will be 
# displayed.

def find_image():
    """This function allows the user to select all the parameters to find an image.
    It saves them directly on their /work directory"""

    cities_menu = widgets.Text(placeholder='Ex: Toulouse, Paris, New-York...')

    lonmax = widgets.FloatText(value=1.5153795, description='Long max:', disabled=False, step=0.001)
    latmax = widgets.FloatText(value=43.668708, description='Lat max:', disabled=False, step=0.001)
    lonmin = widgets.FloatText(value=1.3503956, description='Long min:', disabled=False, step=0.001)
    latmin = widgets.FloatText(value=43.532654, description='Lat min:', disabled=False, step=0.001)

    bbox_menu = widgets.VBox([
        widgets.Label(value="Enter a city:"),
        cities_menu
    ])

    raw_bbox_menu = widgets.Textarea(
        value='1.5153795,43.668708,1.3503956,43.532654',
        placeholder='BBOX',
        disabled=False,
        layout=widgets.Layout(width='50%')
    )

    children = [bbox_menu,
                widgets.VBox([lonmax, latmax, lonmin, latmin]),
                widgets.VBox([
                    widgets.Label(value="Enter a raw BBOX:"),
                    raw_bbox_menu
                ])]

    tab = widgets.Tab()
    tab.children = children
    tab.set_title(0, 'Cities')
    tab.set_title(1, 'Bounding Box')
    tab.set_title(2, 'Raw Bounding Box')

    global_output = widgets.Output()
    out = widgets.Output()
    button = widgets.Button(description='Validate')

    display(tab)
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
            clear_output(wait=True)
            get_collection(bbox)

    button.on_click(click_bbox)


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
    if (tab.selected_index == 0):
        polygon, bbox, place_name = city_polygon_bbox(cities_menu.value)
        with out:
            print(place_name)
    elif (tab.selected_index == 1):
        bbox = [lonmax.value, latmax.value, lonmin.value, latmin.value]
    elif (tab.selected_index == 2):
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


def get_collection(bbox):
    """This function allows the user to select the collection parameter 
    
    Parameters
    ----------
    bbox: tuple
        The bounding box chosen by user
    """

    collection_widget = widgets.Dropdown(
        options=COLLECTION_OPTIONS,
        description='Collection',
    )
    button = widgets.Button(description='Validate')
    out = widgets.Output()
    display(collection_widget)
    display(button)
    display(out)

    def click_collection(b):
        with out:
            clear_output(wait=True)
            get_layer(collection_widget, bbox)

    button.on_click(click_collection)


def get_layer(collection_widget, bbox):
    """This function allows the user to select the layer he wants, 
    linked to the collection chosen before.
    
    Parameters
    ----------
    collection_widget : ipywidgets.dropdown()
        dropdown widget for selecting the collection.
    bbox: tuple
        The bounding box chosen by user
    """

    (sattellite, collection) = collection_widget.value
    
    c = MundiCatalogue()
    wms = c.get_collection(sattellite).mundi_wms(collection)

    projection = 'EPSG:4326'

    layers = list(wms.contents)
    
    
    layer_widget = widgets.Dropdown(
        options=layers,
        description='Layer',
        value=str(layers[1]),
    )
    button = widgets.Button(description='Validate')
    out = widgets.Output()
    display(layer_widget)
    display(button)
    display(out)

    def click_layer(b):
        with out:
            clear_output(wait=True)
            get_param(collection_widget, layer_widget, bbox)

    button.on_click(click_layer)


def get_param(collection_widget, layer_widget, bbox):
    """This function allows the user to define the image parameters
    (timedelta, title, filename, height, width).
    
    Parameters
    ----------
    collection_widget : ipywidgets.dropdown()
        dropdown widget for selecting the collection
    layer_widget : ipywidgets.dropdown()
        dropdown widget for selection the image layer
    bbox: tuple
        The bounding box chosen by user
    """

    (satellite, _) = collection_widget.value
    date_dict = DATE_DICT
    start_date_widget = widgets.DatePicker(
        description='Starting Date',
        value=date_dict[satellite],
        disabled=False
    )
    current_date_widget = widgets.DatePicker(
        description='Final date',
        value=datetime.date.today(),
        disabled=False)

    bbox_menu = widgets.VBox([
        widgets.Label(value="Select your date :"),
        current_date_widget
    ])

    children = [bbox_menu, widgets.VBox([start_date_widget, current_date_widget])]

    tab = widgets.Tab()
    tab.children = children
    tab.set_title(0, 'Best img nearest date')
    tab.set_title(1, 'Best img in timedelta')

    title_widget = widgets.Text(
        value='',
        placeholder='Title to print on the image',
        description='Title',
        disabled=False
    )
    file_name_widget = widgets.Text(
        value='',
        placeholder='File name of the image',
        description='File name',
        disabled=False
    )
    height_widget = widgets.IntText(
        value=480,
        description='Height',
        disabled=False
    )
    width_widget = widgets.IntText(
        value=720,
        description='Width',
        disabled=False
    )
    button_widget = widgets.Button(
        description='Download Image',
        disabled=False,
        button_style='',
        tooltip='Click me',
    )
    output_widget = widgets.Output(
    )
    output_gif = widgets.Output(
    )

    display(tab)
    display(title_widget)
    display(file_name_widget)
    display(height_widget)
    display(width_widget)
    display(button_widget)
    display(output_widget)
    display(output_gif)

    def click_get_param(b):
        with output_widget:
            if (title_widget.value == '') and (file_name_widget.value == ''):
                file_name_widget.value = "your_image"
            elif (file_name_widget.value == ''):
                file_name_widget.value = title_widget.value

            download_images(bbox, collection_widget.value, layer_widget.value, start_date_widget.value,
                            current_date_widget.value, title_widget.value, file_name_widget.value, height_widget.value,
                            width_widget.value)

    button_widget.on_click(click_get_param)


def sentinel_images_display():
    """ This function allows to display one of the img which are in the sentinel_images folder"""

    accepted_extensions = ["png"]
    filenames = [fn for fn in os.listdir(SAVE_FOLDER_IMAGES) if fn.split(".")[-1] in accepted_extensions]
    display_file_widget = widgets.Dropdown(
        options=filenames,
        description='Image To Display',
    )
    button_dis = widgets.Button(description='Display this image')
    out_wid_dis = widgets.Output()

    def click_display(b):
        with out_wid_dis:
            clear_output(wait=True)
            print("Your image has been successfully displayed !")
            print("")
            display(HTML('<img src="{}">'.format('../../work/sentinel2_images/' + display_file_widget.value)))

    button_dis.on_click(click_display)

    display(display_file_widget)
    display(button_dis)
    display(out_wid_dis)


def sentinel_images_delete():
    """ This function allows to delete one of the img which are in the sentinel_images folder"""

    images = []
    accepted_extensions = ["png"]
    filenames = [fn for fn in os.listdir(SAVE_FOLDER_IMAGES) if fn.split(".")[-1] in accepted_extensions]
    k = len(filenames)
    fig = plt.figure(figsize=(25, 20))
    columns = 5
    i = 0
    for file in filenames:
        plt.subplot(k / columns + 1, columns, i + 1)
        plt.title(file)
        i += 1
        plt.imshow(Image.open(f"{SAVE_FOLDER_IMAGES}{file}"))

    delete_file_widget = widgets.Dropdown(
        options=filenames,
        description='File To Delete',
    )

    button_del = widgets.Button(description='Delete this file')
    out_wid_del = widgets.Output()

    box_layout = widgets.Layout(
        border='',
        margin='0px 20px 20px 0px',
        padding='5px 60px 5px 60px')

    vbox1 = widgets.VBox([widgets.Label('Delete some img'), delete_file_widget, button_del, out_wid_del])
    vbox1.layout = box_layout

    display(widgets.HBox([vbox1]))

    def click_file(b):
        with out_wid_del:
            clear_output(wait=True)
            os.remove(f'{SAVE_FOLDER_IMAGES}{delete_file_widget.value}')
            print(f'File {delete_file_widget.value} deleted')

    button_del.on_click(click_file)