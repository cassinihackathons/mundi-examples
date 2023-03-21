import os 

import geopandas as gpd
import math
from descartes import PolygonPatch
from matplotlib import pyplot as plt
import osmnx
import folium
from IPython.display import display
from PIL import Image

os.environ["PROJ_LIB"] = r"c:\Users\a766113\AppData\Local\Continuum\anaconda3\envs\mundi-final\Library\share"


# --------------------------
#  TOOLBOX - BBOX
# --------------------------
def height2width(bbox, height):
    """Get optimized width for a given height regarding a known bbox"""
    x1 = bbox[0]
    y1 = bbox[1]
    x2 = bbox[2]
    y2 = bbox[3]
    return int(height * (x2 - x1) / (y2 - y1))


def width2height(bbox, width):
    """Get optimized height for a given width regarding a known bbox"""
    x1 = bbox[0]
    y1 = bbox[1]
    x2 = bbox[2]
    y2 = bbox[3]
    return int(width * (y2 - y1) / (x2 - x1))


# --------------------------
#  POLYGON/MAP HELPERS
# --------------------------
def country_polygon_bbox(country_name):
    """
    Get the polygon and bbox of a country

    :param country_name: the English name of a country (eg, 'Switzerland', 'Germany'...)
    :return: a tuple of a shapely [multi]polygon and a bbox (xmin, ymin, xmax, ymax)
    """

    # get bbox from a given polygon
    # function found here: https://www.programcreek.com/python/example/95238/shapely.geometry.box
    def polygon_box(min_x, min_y, max_x, max_y):
        f_min_x, f_min_y = int(math.floor(min_x)), int(math.floor(min_y))
        c_max_x, c_max_y = int(math.ceil(max_x)), int(math.ceil(max_y))
        offset = (f_min_x, f_min_y)
        polygon_width = c_max_x - f_min_x
        polygon_height = c_max_y - f_min_y
        return offset, polygon_width, polygon_height

    # retrieve all countries
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

    # only keep geometry and name columns
    countries = world[['geometry', 'name']]

    # get our country of interest
    country = countries[countries['name'] == country_name]
    polygon = country.geometry.values[0]

    # get polygon coordinates & dimensions
    (x, y), w, h = polygon_box(*polygon.bounds)
    bbox = x, y, x + w, y + h

    return polygon, bbox


def display_country_on_world_map(country_name, fig_size=18, color='red'):
    """
    Display the polygon of a country on a static map

    :param country_name: name of the country to display, eg 'Switzerland', 'Germany', etc
    :param fig_size: size of the figure. Defaults to 20
    :param color: color to use for the country, as a string. Defaults to 'red'
    """

    def plot_country_patch(ax):
        # plot a country on the provided axes
        country = world[world.name == country_name]
        country_features = country.__geo_interface__['features']
        country_type_coordinates = {
            'type': country_features[0]['geometry']['type'],
            'coordinates': country_features[0]['geometry']['coordinates']
        }
        ax.add_patch(PolygonPatch(country_type_coordinates, fc=color, ec="black", alpha=0.85, zorder=2))

    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

    # plot the whole world
    axe_world = world.plot(figsize=(fig_size, 30), edgecolor=u'gray')

    plot_country_patch(axe_world)

    plt.ylabel('Latitude')
    plt.xlabel('Longitude')

    plt.show()


def city_polygon_bbox(city_name):
    """
    Get the polygon, the bounding box and the place name (with region, country, etc) of a city

    :param city_name: the city of intereset (eg 'Toulouse')
    :return: a tuple of (shapely Polygon, bbox [east, north, west, south], place name [string])
    """
    city = osmnx.gdf_from_place(city_name)

    # retrieve data from row
    row = city.loc[0]
    polygon = row.get('geometry')
    bbox_east = row.get('bbox_east')
    bbox_north = row.get('bbox_north')
    bbox_south = row.get('bbox_south')
    bbox_west = row.get('bbox_west')
    place_name = row.get('place_name')

    # build bbox
    bbox = (bbox_east, bbox_north, bbox_west, bbox_south)

    return polygon, bbox, place_name


def display_wms(polygon, bbox, wms, wms_layers, time, height=512):
    """
    Display polygons and their satellite img using WMS and an interactive map. Use only in Jupyter Notebooks.

    :param polygon: a shapely [Multi]Polygon for the area of interest (AOI)
    :param bbox: the bbox of the AOI
    :param height: the height of the satellite image. Width is computed to keep proportions. Defaults to 512
    :param wms_layers: a string mapped to the layers of interest. Can take two values:
    '0' (only first layer) or 'all' (all layers)
    :param time: date range for the satellite image formatted as 'YYYY-MM-DD' or 'YYYY-MM-DD/YYYY-MM-DD'
    (eg '2018-12-27/2019-01-10')
    """
    map_center = polygon.centroid
    m = folium.Map([map_center.y, map_center.x], zoom_start=3, tiles='cartodbpositron')
    folium.GeoJson(polygon).add_to(m)
    folium.LatLngPopup().add_to(m)
    display(m)

    projection = 'EPSG:4326'
    width = height2width(bbox, height)

    layers = list(wms.contents)

    if wms_layers == '0':
        # get layer from WMS
        print(wms[layers[0]].title)
        img = wms.getmap(layers=[wms[layers[1]].name],
                         srs=projection,
                         bbox=bbox,
                         size=(width, height),
                         format='image/png',
                         time=time,
                         showlogo=False,
                         transparent=False,
                         maxcc=30)

        display(Image.open(img))

    elif wms_layers == 'all':
        # get layers from WMS
        for lay in layers:
            print(wms[lay].title)
            img = wms.getmap(layers=[wms[lay].name],
                             srs=projection,
                             bbox=bbox,
                             size=(width, height),
                             format='image/png',
                             time=time,
                             showlogo=False,
                             transparent=False,
                             maxcc=30)

            display(Image.open(img))
