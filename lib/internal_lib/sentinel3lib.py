# Library containing all the useful functions for the mundi_S3_images_search notebook
# Author : Lenoir d'Espinasse Guillaume
# Contact email : guillaume.lenoirdespinasse@atos.net

import datetime
import glob
import imageio
import matplotlib.pyplot as plt
import numpy as np
import os
import urllib
import requests

import ipywidgets as widgets
from IPython.display import clear_output, display, HTML
from PIL import Image, ImageDraw, ImageFont, ImageOps

# --------------------------
#  Global Variables
# --------------------------

# Logos URL
URL_LOGO_WHITE = 'https://mundiwebservices.com/build/assets/Mundi-Logo-CMYK-white.png'
URL_LOGO_COLORS = 'https://mundiwebservices.com/build/assets/Mundi-Logo-CMYK-colors.png'

# Path to the Mundi Font
TTF_PATH = "/home/jovyan/lib/dependencies/fonts/poppins-light.ttf"

sentinel3_start_date = datetime.date(2016, 10, 15)

S3_LAYERS = ['ENHANCED-TRUE-COLOR','ENHANCED-TRUE-COLOR-2','OLCI-NATURAL-COLOR','FALSE-COLOR-1','FALSE-COLOR-2', 'VEGETATION-MONITORING-INDEX','NDBI']

SAVE_FOLDER = "/home/jovyan/work/sentinel3_images/"
SAVE_FOLDER_IMAGES = f"{SAVE_FOLDER}images/"
SAVE_FOLDER_GIF = f"{SAVE_FOLDER}gif/"

# --------------------------
#  Useful functions
# --------------------------

def setup():
    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)
        
        
def get_image(bbox, height, width, layers, start_date, stop_date):
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
    xmin = bbox[2]
    ymin = bbox[3]
    xmax = bbox[0]
    ymax = bbox[1]
    
    url = 'https://creodias.sentinel-hub.com/ogc/wms/891d1d73-cdb0-43ba-a453-b34a6e1dc6e8?SERVICE=WMS&REQUEST=GetMap&TRANSPARENT=true&LAYERS='+layers+'&VERSION=1.1.1&MAXCC=10&FORMAT=image%2Fpng&STYLES=&showLogo=false&time='+str(start_date)+'%2F'+str(stop_date)+'&width='+str(width)+'&height='+str(height)+'&SRS=EPSG%3A4326&bbox='+str(xmin)+'%2C'+str(ymin)+'%2C'+str(xmax)+'%2C'+str(ymax)
    
    img = requests.get(url)
    
    return img


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


def download_images(bbox, layers, start_date, stop_date,
                    title, delta_days, height, width):
    """This functions download all the images with the given parameters

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
    files = glob.glob(f'{SAVE_FOLDER_IMAGES}*')
    for f in files:
        os.remove(f)
    
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
        img = get_image(bbox, height, width, layers, current_date, next_date)
        files = glob.glob(f'{SAVE_FOLDER_IMAGES}*')
        f = open(r'/home/jovyan/work/sentinel3_images/images/'+str(cpt)+'.png', 'wb')
        f.write(img.content)
        f.close()
        image = Image.open(f'{SAVE_FOLDER_IMAGES}'+str(cpt)+'.png')
        image = image.convert('RGB')
        # Choosing fonts for the date, title and subtitle
        # The characters are written in white with a black thin border
        border = 1
        fnt = ImageFont.truetype(TTF_PATH, int(width / 45))
        fnt2 = ImageFont.truetype(TTF_PATH, int(width / 30))
        fnt3 = ImageFont.truetype(TTF_PATH, int(width / 55))
        draw = ImageDraw.Draw(image)
        date = str(next_date)
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

        images.append(np.array(image))
        image.save(SAVE_FOLDER_IMAGES + str(cpt)+'.png')
            
        current_date = next_date
        cpt += 1
        clear_output(wait=True)
    print("All img downloaded on time !")

# --------------------------
#  GIF creation functions
# --------------------------
    
# Main function
# By calling this function, widgets will be displayed and each time the user
# clicks on validate, a new function will be called and new widgets will be
# displayed.
def create_gif():
    """This function allows the user to select all the parameters to create their own GIFs.
    It saves them directly on their /work directory
    """

    lonmax = widgets.FloatText(value=-5.370118, description='Long max:', disabled=False, step=0.001)
    latmax = widgets.FloatText(value=41.347753, description='Lat max:', disabled=False, step=0.001)
    lonmin = widgets.FloatText(value=9.791015, description='Long min:', disabled=False, step=0.001)
    latmin = widgets.FloatText(value=51.270301, description='Lat min:', disabled=False, step=0.001)

    bbox_menu = widgets.VBox([lonmax, latmax, lonmin, latmin])

    raw_bbox_menu = widgets.Textarea(
        value='-5.370118,41.347753,9.791015,51.270301',
        placeholder='BBOX',
        disabled=False,
        layout=widgets.Layout(width='50%')
    )

    countries_menu = widgets.Text(placeholder='Ex: Toulouse, Paris, New-York...')

    children = [bbox_menu,
                widgets.VBox([
                    widgets.Label(value="Enter a raw BBOX:"),
                    raw_bbox_menu
                ])]

    tab = widgets.Tab()
    tab.children = children
    tab.set_title(0, 'Bounding Box')
    tab.set_title(1, 'Raw Bounding Box')

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
        bbox = get_bbox(tab, out, lonmax, latmax, lonmin, latmin, countries_menu, raw_bbox_menu)
        with global_output:
            clear_output(wait=True)
            get_layer_gif(bbox)

    button.on_click(click_bbox)


def get_bbox(tab, out, lonmax, latmax, lonmin, latmin, countries_menu, raw_bbox_menu):
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
    if tab.selected_index == 0:
        bbox = [lonmax.value, latmax.value, lonmin.value, latmin.value]
     
    elif tab.selected_index == 1:
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

 
def get_layer_gif(bbox):
    """This function allows the user to select the layer he wants, 
    linked to the collection chosen before.
    
    Parameters
    ----------
    collection_widget : ipywidgets.dropdown()
        dropdown widget for selecting the collection.
    bbox: tuple
        The bounding box chosen by user
    """
    
    layer_widget = widgets.Dropdown(
        options=S3_LAYERS,
        description='Layer',
        value=str(S3_LAYERS[0]),
    )
    button = widgets.Button(description='Validate')
    out = widgets.Output()
    display(layer_widget)
    display(button)
    display(out)

    def click_layer(b):
        with out:
            clear_output(wait=True)
            get_param_gif(bbox,layer_widget)

    button.on_click(click_layer)

    
def get_param_gif(bbox, layer_widget):
     
    start_date_widget = widgets.DatePicker(
        description='Starting Date',
        value=datetime.date.today() - datetime.timedelta(20),
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
    delta_days_widget = widgets.IntText(
        value=1,
        description='Time frame to acquire data',
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
    display(delta_days_widget)
    display(height_widget)
    display(width_widget)
    display(button_widget)
    display(output_widget)
    display(output_gif)

    def click_gif(b):
        with output_widget:
            download_images(bbox, layer_widget.value, start_date_widget.value,
                            stop_date_widget.value, title_widget.value, delta_days_widget.value,
                            height_widget.value, width_widget.value)

    button_widget.on_click(click_gif)


def gif_folder():
    
    """This function allows to display all images available in the sentinel3_images/images folder. It allows to delete some of them
    (too cloudy for example) and to define all parameters needed to create the GIF file.
    """
    
    accepted_extensions = ["png"]
    filenames = [fn for fn in os.listdir(SAVE_FOLDER_IMAGES) if fn.split(".")[-1] in accepted_extensions]
   
    temp = [int(fn.split('.')[0]) for fn in filenames]
    temp = sorted(temp)
    final_filenames = [f'{elt}.png' for elt in temp]
    k = len(final_filenames)
    plt.figure(figsize=(25, 20))
    columns = 5
    i = 0
    for file in final_filenames:
        plt.subplot(k / columns + 1, columns, i + 1)
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
        description='File Name',
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
            os.remove(f'{SAVE_FOLDER_IMAGES}{file_widget.value}')
            print(f'File {file_widget.value} deleted')

    def click_generate(b):
        with out_wid_create:
            generate_gif_from_folder(duration_widget.value, output_name_widget.value, end_gif_duration_widget.value)

    button_del.on_click(click_file)
    button_widget.on_click(click_generate)

    
def generate_gif_from_folder(duration, output_name, end_gif_duration, folder=SAVE_FOLDER_IMAGES, logo_url=None,
                             sort_key=lambda y: int(y.split(".")[0]), accepted_extensions=None, display_texts=None,
                             display_text_font_size=lambda img: int(img.width / 20)):
    f"""This functions generates the GIF file from the files in your /work/sentinel3_images/images

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
        raise ValueError(f"display_texts' length must be the number of img ({len(display_texts)} vs {len(final_filenames)})")

    # download Mundi logo
    logo_img = None
    if logo_url is not None:
        logo_img = Image.open(urllib.request.urlopen(logo_url))
        logo_img.mode = 'RGBA'

    k = len(final_filenames)
    if display_texts is not None and len(display_texts) != k:
        raise ValueError(f"size of 'display_names' is not equal to the number of files found ({len(display_texts)} vs {k}")

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
    

def display_gif():
    
    """This function allows to search all the GIF files in the /work directory and display the GIF you want
    """
    
    accepted_extensions = ["gif"]
    filenames = [fn for fn in os.listdir(SAVE_FOLDER_GIF) if fn.split(".")[-1] in accepted_extensions]
    file_widget = widgets.Dropdown(
        options=filenames,
        description='File to open',
    )
    button_file = widgets.Button(description='Display GIF')
    out_wid = widgets.Output()
    display(file_widget)
    display(button_file)
    display(out_wid)

    def click_file(b):
        with out_wid:
            clear_output(wait=True)
            print(f"{SAVE_FOLDER_GIF}{file_widget.value}")
            display(HTML('<img src="{}">'.format('../../work/sentinel3_images/gif/' + file_widget.value)))

    button_file.on_click(click_file)

