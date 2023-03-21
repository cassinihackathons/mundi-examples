#!/usr/bin/python
# -*- coding: ISO-8859-15 -*-
# =============================================================================
# Copyright (c) 2019 Mundi Web Services
# Licensed under the 3-Clause BSD License; you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
# https://opensource.org/licenses/BSD-3-Clause
#
# Author : Dr. Abdelghafour Halimi
#
# Contact email: abdelghafour.halimi@atos.net
# =============================================================================

import warnings
warnings.filterwarnings("ignore")

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import folium
from folium import plugins
import datetime
import xarray
import branca
import geojsoncontour

from mpl_toolkits.basemap import Basemap

import ipywidgets as widgets
import ftputil
import pandas as pd
import os
from ipywidgets import interact, interactive, fixed, interact_manual
import math
from pathlib import Path
from collections import Iterable
from PIL import Image


### Cmems Functions ##############################################################

class Cmems:
################################# MODEL AND SATELLITE PRODUCTS #################################################
################################################################################################################

############################################################################################
#------------------------------------------------------------------------------------------
#       DOWNLOAD THE FILE  (For MODEL AND SATELLITE PRODUCTS)
#------------------------------------------------------------------------------------------
###########################################################################################   
    @staticmethod
    def download_Product(user,password,Product):
        ########## CASE 1 (Product=='Model') : Get the list of all model products offered by the cmems catalog
        
        if Product=='Model':
            Model_products=[]
            # connect to CMEMS FTP
            with ftputil.FTPHost('nrt.cmems-du.eu', user, password) as ftp_host: 
                ftp_host.chdir('Core')
                product_list=[]
                product_list = ftp_host.listdir(ftp_host.curdir)
                for product in product_list:
                    items = product.split('_')
                    # conditions to select only model products
                    if 'OBSERVATIONS' not in items and  'MULTIOBS' not in items and 'INSITU' not in items:
                        Model_products.append(product)
            data = {'MODEL PRODUCTS': []}
        #-----------------------------------------------------------------------------------------------------
        
        ########## CASE 2 (Product=='Satellite') : Get the list of all satellite products offered by the cmems catalog 
        
        elif Product=='Satellite':  
            Model_products=[]
            # connect to CMEMS FTP
            with ftputil.FTPHost('nrt.cmems-du.eu', user, password) as ftp_host: 
                ftp_host.chdir('Core')
                product_list=[]
                product_list = ftp_host.listdir(ftp_host.curdir)
                for product in product_list:
                    items = product.split('_')
                    # conditions to select only satellite products
                    if 'MULTIOBS' in items or 'OBSERVATIONS' in items  and 'INSITU' not in items:
                        Model_products.append(product)
            data = {'SATELLITE OBSERVATION PRODUCTS': []}
       #-----------------------------------------------------------------------------------------------------
            
            
        ########## Initialize the widgets ------------------------------------------------------------------
        
        style = {'description_width': 'initial'}
        if Product=='Model':
            x_widget = widgets.Dropdown(layout={'width': 'initial'},
                options=Model_products,
                value=Model_products[4],
                description='Product:',
                disabled=False)
        elif Product=='Satellite':
            x_widget = widgets.Dropdown(layout={'width': 'initial'},
                options=Model_products,
                value=Model_products[52],
                description='Product:',
                disabled=False)
                
        product_name=x_widget.value
        with ftputil.FTPHost('nrt.cmems-du.eu', user, password) as ftp_host: 
            ftp_host.chdir("Core"+'/'+product_name)
            product_list2 = ftp_host.listdir(ftp_host.curdir)
        y_widget = widgets.RadioButtons(layout={'width': 'initial'},options=product_list2,value=product_list2[0],description='Available data type  :',style=style)

        product_name2=y_widget.value
        with ftputil.FTPHost('nrt.cmems-du.eu', user, password) as ftp_host: 
            ftp_host.chdir("Core"+'/'+product_name +'/'+product_name2)
            product_list3 = ftp_host.listdir(ftp_host.curdir)  
        z_widget = widgets.Dropdown(layout={'width': 'initial'},options=product_list3,value=product_list3[3],description='Year:')

        product_name3=z_widget.value
        with ftputil.FTPHost('nrt.cmems-du.eu', user, password) as ftp_host: 
            ftp_host.chdir("Core"+'/'+product_name +'/'+product_name2+'/'+product_name3)
            product_list4 = ftp_host.listdir(ftp_host.curdir)
        w_widget = widgets.Dropdown(layout={'width': 'initial'},options=product_list4,value=product_list4[5],description='Month:')

        product_name4=w_widget.value
        with ftputil.FTPHost('nrt.cmems-du.eu', user, password) as ftp_host: 
            ftp_host.chdir("Core"+'/'+product_name +'/'+product_name2+'/'+product_name3+'/'+product_name4)
            product_list5 = ftp_host.listdir(ftp_host.curdir)
        i_widget = widgets.Dropdown(layout={'width': 'initial'},options=product_list5,value=product_list5[3],description='File:')
        #-----------------------------------------------------------------------------------------------------



        ############# Define a function that updates the content of (y_widget,z_widget,w_widget,i_widget) based on what we select for x_widget
        def update(*args):
            product_name=x_widget.value
            
            # Get the list of the available data offered by the selected product
            with ftputil.FTPHost('nrt.cmems-du.eu', user, password) as ftp_host: 
                ftp_host.chdir("Core"+'/'+product_name)
                product_list2 = ftp_host.listdir(ftp_host.curdir)
            
            # Get the content of y_widget based on x_widget.value
            y_widget.options=product_list2

            product_name2=y_widget.value
            with ftputil.FTPHost('nrt.cmems-du.eu', user, password) as ftp_host: 
                ftp_host.chdir("Core"+'/'+product_name +'/'+product_name2)
                product_list3 = ftp_host.listdir(ftp_host.curdir)
                
            # Get the content of the widgets based on our selection for different cases:
            
            # case 1 : Get the content of the widgets based on the value of y_widget
            if 'nc' in product_list3[1]:
                z_widget.options=product_list3
                z_widget.description='File'
                w_widget.options=['']
                i_widget.options=['']
                w_widget.description='option'
                i_widget.description='option'
                netcdf_files=[]
                netcdf_files=product_list3
            else:
                z_widget.options=product_list3
                z_widget.description='Year'
                product_name3=z_widget.value
                with ftputil.FTPHost('nrt.cmems-du.eu', user, password) as ftp_host: 
                    ftp_host.chdir("Core"+'/'+product_name +'/'+product_name2+'/'+product_name3)
                    product_list4 = ftp_host.listdir(ftp_host.curdir)
                    
                # case 2 : Get the content of the widgets based on the value of z_widget
                if 'nc' in product_list4[1]:
                    w_widget.options=product_list4
                    w_widget.description='File'
                    i_widget.options=['']
                    netcdf_files=[]
                    netcdf_files=product_list4
                else:
                    w_widget.options=product_list4
                    w_widget.description='Month'
                    product_name4=w_widget.value
                    with ftputil.FTPHost('nrt.cmems-du.eu', user, password) as ftp_host: 
                        ftp_host.chdir("Core"+'/'+product_name +'/'+product_name2+'/'+product_name3+'/'+product_name4)
                        product_list5 = ftp_host.listdir(ftp_host.curdir)
                        
                    # case 3 : Get the content of the widgets based on the value of w_widget
                    if 'nc' in product_list5[1]:
                        i_widget.options=product_list5#['List of netCdf Files']
                        i_widget.description='File'
                        netcdf_files=[]
                        netcdf_files=product_list5
                    else:
                        i_widget.options=product_list5
                        i_widget.description='day'

            return (z_widget.value,w_widget.value,i_widget.value)

        # update the content of the widgets according to our selection 
        x_widget.observe(update,'value')
        y_widget.observe(update,'value')
        z_widget.observe(update,'value')
        w_widget.observe(update,'value')
        ####################-------------------------------------------------------------------------------------------------


        ######## Define the download procedure using the ftp protocol
        def random_function(x, y, z, w, i):
            
            ###### get the downloading path 
            path=[x,y,z,w,i]
            path_new=[]
            file=[]
            for i in path:
                if i != 'List of netCdf Files' and i != '':
                    path_new.append(i)
            file=path_new[-1]

            path2 = "Core"
            for i in range(len(path_new)):
                path2 = path2+'/'+str(path_new[i])
            filepath2= path2
            ncdf_file_name2=file
            #-----------------------------------------

            # define the downloading button
            button = widgets.Button(description='''Download The File''')
            out = widgets.Output()
            def on_button_clicked(_):
                  # "linking function with output"
                with out:
                    #try:
                    output_directory=[]
                    # set the output_directory of the file
                    if Product=='Model':
                        if os.getcwd() == '/home/jovyan/public':
                            output_directory='/home/jovyan/work'+'/cmems_data/01_Model_product'
                        else:
                            output_directory=os.getcwd()+'/cmems_data/01_Model_product'
                    elif Product=='Satellite':
                        if os.getcwd() == '/home/jovyan/public':
                            output_directory='/home/jovyan/work'+'/cmems_data/02_Satellite_product'
                        else:
                            output_directory=os.getcwd()+'/cmems_data/02_Satellite_product'
                    #--------------------------------------------------------------------                            
                    # creating a folder using the output_directory  
                    p = Path(output_directory)
                    p.mkdir(parents=True, exist_ok=True)  
                    # downloading the file using the ftp protocol
                    host = 'nrt.cmems-du.eu'
                    print(f"Downloading The File '{ncdf_file_name2}' in {output_directory}")
                    with ftputil.FTPHost(host, user, password) as ftp_host: 
                        cwd = os.getcwd()
                        os.chdir(output_directory)
                        try:
                            ftp_host.download(filepath2, ncdf_file_name2)  # remote, local
                            print("Done")
                        except:
                            print("Downloading can't be done for this file, please run the function again and choose a netCDF file")
                        os.chdir(cwd)
                    #except:
                        #print("Downloading can't be done, please run the function again and choose a netCDF file")
                return(ncdf_file_name2)  

            # linking button and function together using a button's method
            button.on_click(on_button_clicked)
            # displaying button and its output together
            aa=widgets.VBox([button,out])

            return(aa)
        #----------------------------------------------------------------------------------------
        
        # display the interaction between the widgets 
        display(pd.DataFrame(data=data))
        interact(random_function,
                 x = x_widget,
                 y = y_widget,
                 z = z_widget,
                 w = w_widget,
                 i = i_widget);

        return(update)
    

###############################################################################################################    
#--------------------------------------------------------------------------------------------
#       READ THE DOWNLOADED FILE  (For MODEL AND SATELLITE PRODUCTS)
#--------------------------------------------------------------------------------------------
###############################################################################################################    
    @staticmethod
    def read_File(update,Product):
        # get the name of the selected file
        for i in update():
            if 'nc' in i:
                file=i 
                
        # get the current directory of the file        
        if Product=='Model':        
            if os.getcwd() == '/home/jovyan/public':
                output_directory='/home/jovyan/work'+'/cmems_data/01_Model_product'
            else:
                output_directory=os.getcwd()+'/cmems_data/01_Model_product'
        elif Product=='Satellite': 
            if os.getcwd() == '/home/jovyan/public':
                output_directory='/home/jovyan/work'+'/cmems_data/02_Satellite_product'
            else:
                output_directory=os.getcwd()+'/cmems_data/02_Satellite_product'
                
        # reading the netcdf file 
        dataset = output_directory+f'/{file}'    
        ds = xarray.open_dataset(dataset)
        
        # get the list of the parameters of the netcdf file
        list_parm_deleted=['time','lat','lon','depth','grid_mapping','x','y','longitude','latitude','LONGITUDE','LATITUDE','time_bnds']
        full_list=list(ds.variables)   
        selected_list=[]
        selected_list_name=[]
        for i in full_list:
            if not i in list_parm_deleted:
                selected_list.append(i)
                try:
                    selected_list_name.append(ds[i].attrs['standard_name'])
                except:
                    try:
                        selected_list_name.append(ds[i].attrs['long_name'])
                    except:
                        selected_list_name.append(i)
        return(ds,selected_list,selected_list_name,dataset)

    
################################################################################################################    
#--------------------------------------------------------------------------------------------
#       DISPLAY THE PARAMETERS OF THE FILE  (For MODEL PRODUCTS)
#--------------------------------------------------------------------------------------------
###############################################################################################################    
    @staticmethod
    def display_param_model(ds,selected_list,selected_list_name):
        ########## Initialize the widgets ------------------------------------------------------------------

        dictionary = dict(zip(selected_list_name, selected_list))
        if len(selected_list_name) < 4:
            x_widget = widgets.Dropdown(layout={'width': 'initial'},
                options=selected_list_name,  
                value=selected_list_name[0],   
                description='Parameters:',
                disabled=False)
        else:
            x_widget = widgets.Dropdown(layout={'width': 'initial'},
                options=selected_list_name,  #selected_list,
                value=selected_list_name[4],   #selected_list[0],
                description='Parameters:',
                disabled=False)
        style = {'description_width': 'initial'}
        varb=dictionary[x_widget.value]
        if len(ds[dictionary[x_widget.value]].shape) < 4:
            n_widget = widgets.Label(value="This parameter does not allow a depth analysis")
            y_widget = widgets.Dropdown(layout={'width': 'initial'},description='Longitude:')
            z_widget = widgets.Dropdown(layout={'width': 'initial'},description='Latitude:')
        else:    
            n_widget = widgets.Label(value="Please select a specific (Longitude,Latitude) to build also a depth analysis figure")
            y_widget = widgets.Dropdown(layout={'width': 'initial'},description='Longitude:')
            z_widget = widgets.Dropdown(layout={'width': 'initial'},description='Latitude:')
            if 'lon' in list(ds.variables):
                if 'x' in list(ds.variables):
                    y_widget.options=sorted(list(set(np.asarray(ds[varb]['x'][:]))))
                    z_widget.options=sorted(list(set(np.asarray(ds[varb]['y'][:]))))
                    try:
                        y_widget.value=sorted(list(set(np.asarray(ds[varb]['x'][:]))))[400]
                        z_widget.value=sorted(list(set(np.asarray(ds[varb]['y'][:]))))[550]
                    except:
                        y_widget.value=sorted(list(set(np.asarray(ds[varb]['x'][:]))))[0]
                        z_widget.value=sorted(list(set(np.asarray(ds[varb]['y'][:]))))[0]
                else:
                    y_widget.options=sorted(list(set(np.asarray(ds[varb]['lon'][:]))))
                    z_widget.options=sorted(list(set(np.asarray(ds[varb]['lat'][:]))))
                    try:
                        y_widget.value=sorted(list(set(np.asarray(ds[varb]['lon'][:]))))[400]
                        z_widget.value=sorted(list(set(np.asarray(ds[varb]['lat'][:]))))[550]
                    except:
                        y_widget.value=sorted(list(set(np.asarray(ds[varb]['lon'][:]))))[0]
                        z_widget.value=sorted(list(set(np.asarray(ds[varb]['lat'][:]))))[0]

            elif 'longitude' in list(ds.variables):  
                if 'x' in list(ds.variables):
                    y_widget.options=sorted(list(set(np.asarray(ds[varb]['x'][:]))))
                    z_widget.options=sorted(list(set(np.asarray(ds[varb]['y'][:]))))
                    try:
                        y_widget.value=sorted(list(set(np.asarray(ds[varb]['x'][:]))))[400]
                        z_widget.value=sorted(list(set(np.asarray(ds[varb]['y'][:]))))[550]
                    except:
                        y_widget.value=sorted(list(set(np.asarray(ds[varb]['x'][:]))))[0]
                        z_widget.value=sorted(list(set(np.asarray(ds[varb]['y'][:]))))[0]
                else:
                    y_widget.options=sorted(list(set(np.asarray(ds[varb]['longitude'][:]))))
                    z_widget.options=sorted(list(set(np.asarray(ds[varb]['latitude'][:]))))
                    try:
                        y_widget.value=sorted(list(set(np.asarray(ds[varb]['longitude'][:]))))[400]
                        z_widget.value=sorted(list(set(np.asarray(ds[varb]['latitude'][:]))))[550]
                    except:
                        y_widget.value=sorted(list(set(np.asarray(ds[varb]['longitude'][:]))))[0]
                        z_widget.value=sorted(list(set(np.asarray(ds[varb]['latitude'][:]))))[0]

            elif 'LONGITUDE' in list(ds.variables):   
                if 'x' in list(ds.variables):
                    y_widget.options=sorted(list(set(np.asarray(ds[varb]['x'][:]))))
                    z_widget.options=sorted(list(set(np.asarray(ds[varb]['y'][:]))))
                    try:
                        y_widget.value=sorted(list(set(np.asarray(ds[varb]['x'][:]))))[400]
                        z_widget.value=sorted(list(set(np.asarray(ds[varb]['y'][:]))))[550]
                    except:
                        y_widget.value=sorted(list(set(np.asarray(ds[varb]['x'][:]))))[0]
                        z_widget.value=sorted(list(set(np.asarray(ds[varb]['y'][:]))))[0]
                else:
                    y_widget.options=sorted(list(set(np.asarray(ds[varb]['LONGITUDE'][:]))))
                    z_widget.options=sorted(list(set(np.asarray(ds[varb]['LATITUDE'][:]))))
                    try:
                        y_widget.value=sorted(list(set(np.asarray(ds[varb]['LONGITUDE'][:]))))[400]
                        z_widget.value=sorted(list(set(np.asarray(ds[varb]['LATITUDE'][:]))))[550]
                    except:
                        y_widget.value=sorted(list(set(np.asarray(ds[varb]['LONGITUDE'][:]))))[0]
                        z_widget.value=sorted(list(set(np.asarray(ds[varb]['LATITUDE'][:]))))[0]
        #---------------------------------------------------------------------------------------------------


        ############# Define a function that updates the content of (y_widget,z_widget,n_widget) based on what we select for x_widget
        def update_2(*args):
            param_name=dictionary[x_widget.value]
            varb=param_name
            if len(ds[varb].shape) < 4:
                y_widget.options=['']
                z_widget.options=['']
                n_widget.value="This parameter does not allow a depth analysis"
                variable = ds.variables[varb][:]
                vmin=variable[0,:,:].min()
                vmax=variable[0,:,:].max()
            else:    
                n_widget.value="Please select a specific (Longitude,Latitude) to build also a depth analysis figure"
                if 'lon' in list(ds.variables):
                    if 'x' in list(ds.variables):
                        y_widget.options=sorted(list(set(np.asarray(ds[varb]['x'][:]))))
                        z_widget.options=sorted(list(set(np.asarray(ds[varb]['y'][:]))))
                    else:
                        y_widget.options=sorted(list(set(np.asarray(ds[varb]['lon'][:]))))
                        z_widget.options=sorted(list(set(np.asarray(ds[varb]['lat'][:]))))
                elif 'longitude' in list(ds.variables):  
                    if 'x' in list(ds.variables):
                        y_widget.options=sorted(list(set(np.asarray(ds[varb]['x'][:]))))
                        z_widget.options=sorted(list(set(np.asarray(ds[varb]['y'][:]))))
                    else:
                        y_widget.options=sorted(list(set(np.asarray(ds[varb]['longitude'][:]))))
                        z_widget.options=sorted(list(set(np.asarray(ds[varb]['latitude'][:]))))
                elif 'LONGITUDE' in list(ds.variables):   
                    if 'x' in list(ds.variables):
                        y_widget.options=sorted(list(set(np.asarray(ds[varb]['x'][:]))))
                        z_widget.options=sorted(list(set(np.asarray(ds[varb]['y'][:]))))
                    else:
                        y_widget.options=sorted(list(set(np.asarray(ds[varb]['LONGITUDE'][:]))))
                        z_widget.options=sorted(list(set(np.asarray(ds[varb]['LATITUDE'][:]))))
                variable = ds.variables[varb][:]
                vmin=variable[0,0,:,:].min()
                vmax=variable[0,0,:,:].max()
            return(vmin,vmax)
        
        # update the content of the widgets according to our selection 
        x_widget.observe(update_2,'value')
        n_widget.observe(update_2,'value')
        y_widget.observe(update_2,'value')
        z_widget.observe(update_2,'value')
        #--------------------------------------------------------------------------------------------------------
        
        ####### configure the display according to the selected parameter
        def random_function(x,n,y,z):
            param_name=dictionary[x]
            param_lon=y
            param_lat=z
            style = {'description_width': 'initial'}
            button = widgets.Button(description="Display The Parameter",style=style)
            out = widgets.Output()
            def on_button_clicked(_):
                  # "linking function with output"
                with out:
                    try:
                        varb=param_name
                        var_lon=param_lon
                        var_lat=param_lat
                        
                        # define the longitude (max,min) and latitude (max,min) for the displaying  
                        if 'lon' in list(ds.variables):
                            if 'x' in list(ds.variables):
                                lon_max=ds.variables['x'][:].max()
                                lon_min=ds.variables['x'][:].min()
                                lat_max=ds.variables['y'][:].max()
                                lat_min=ds.variables['y'][:].min()

                                lon_max=np.asscalar(np.asarray(lon_max, dtype=np.float))
                                lon_min=np.asscalar(np.asarray(lon_min, dtype=np.float))

                                lat_max=np.asscalar(np.asarray(lat_max, dtype=np.float))
                                lat_min=np.asscalar(np.asarray(lat_min, dtype=np.float))

                                lons = ds.variables['x'][:]
                                lats = ds.variables['y'][:]
                            else:
                                lon_max=ds.variables['lon'][:].max()
                                lon_min=ds.variables['lon'][:].min()
                                lat_max=ds.variables['lat'][:].max()
                                lat_min=ds.variables['lat'][:].min()

                                lon_max=np.asscalar(np.asarray(lon_max, dtype=np.float))
                                lon_min=np.asscalar(np.asarray(lon_min, dtype=np.float))

                                lat_max=np.asscalar(np.asarray(lat_max, dtype=np.float))
                                lat_min=np.asscalar(np.asarray(lat_min, dtype=np.float))

                                lons = ds.variables['lon'][:]
                                lats = ds.variables['lat'][:]

                        elif 'longitude' in list(ds.variables):   
                            if 'x' in list(ds.variables):
                                lon_max=ds.variables['x'][:].max()
                                lon_min=ds.variables['x'][:].min()
                                lat_max=ds.variables['y'][:].max()
                                lat_min=ds.variables['y'][:].min()

                                lon_max=np.asscalar(np.asarray(lon_max, dtype=np.float))
                                lon_min=np.asscalar(np.asarray(lon_min, dtype=np.float))

                                lat_max=np.asscalar(np.asarray(lat_max, dtype=np.float))
                                lat_min=np.asscalar(np.asarray(lat_min, dtype=np.float))

                                lons = ds.variables['x'][:]
                                lats = ds.variables['y'][:]
                            else:
                                lon_max=ds.variables['longitude'][:].max()
                                lon_min=ds.variables['longitude'][:].min()
                                lat_max=ds.variables['latitude'][:].max()
                                lat_min=ds.variables['latitude'][:].min()

                                lon_max=np.asscalar(np.asarray(lon_max, dtype=np.float))
                                lon_min=np.asscalar(np.asarray(lon_min, dtype=np.float))

                                lat_max=np.asscalar(np.asarray(lat_max, dtype=np.float))
                                lat_min=np.asscalar(np.asarray(lat_min, dtype=np.float))

                                lons = ds.variables['longitude'][:]
                                lats = ds.variables['latitude'][:]    


                        elif 'LONGITUDE' in list(ds.variables):   
                            if 'x' in list(ds.variables):
                                lon_max=ds.variables['x'][:].max()
                                lon_min=ds.variables['x'][:].min()
                                lat_max=ds.variables['y'][:].max()
                                lat_min=ds.variables['y'][:].min()

                                lon_max=np.asscalar(np.asarray(lon_max, dtype=np.float))
                                lon_min=np.asscalar(np.asarray(lon_min, dtype=np.float))

                                lat_max=np.asscalar(np.asarray(lat_max, dtype=np.float))
                                lat_min=np.asscalar(np.asarray(lat_min, dtype=np.float))

                                lons = ds.variables['x'][:]
                                lats = ds.variables['y'][:]
                            else:
                                lon_max=ds.variables['LONGITUDE'][:].max()
                                lon_min=ds.variables['LONGITUDE'][:].min()
                                lat_max=ds.variables['LATITUDE'][:].max()
                                lat_min=ds.variables['LATITUDE'][:].min()

                                lon_max=np.asscalar(np.asarray(lon_max, dtype=np.float))
                                lon_min=np.asscalar(np.asarray(lon_min, dtype=np.float))

                                lat_max=np.asscalar(np.asarray(lat_max, dtype=np.float))
                                lat_min=np.asscalar(np.asarray(lat_min, dtype=np.float))

                                lons = ds.variables['LONGITUDE'][:]
                                lats = ds.variables['LATITUDE'][:]  

                        if lon_min <-180 or lat_min < -90  or lon_max > 180 or lat_max >90:
                            lon_min,lat_min,lon_max,lat_max= (-180,-90,180,90)
                            #---------------------------------------------------------------------
                            
                        # case 1 : display the selected parameter on a map without a depth analysis
                        if len(ds[varb].shape) < 3:

                            variable = ds.variables[varb][:]
                            try:
                                variable_title=ds[varb].attrs['standard_name']
                            except:
                                try:
                                    variable_title=ds[varb].attrs['long_name']
                                except:
                                    variable_title=varb
                            lon, lat = np.meshgrid(lons, lats)

                            plt.figure(figsize=(20,7))
                            plt.subplot(121)
                            if lon_min-2 <-180 or lat_min-3 < -90 or lon_max+2 > 180 or lat_max+4.2 >90:
                                map = Basemap(llcrnrlon=lon_min,llcrnrlat=lat_min,urcrnrlon=lon_max,urcrnrlat=lat_max, epsg=4326)
                            else:
                                map = Basemap(llcrnrlon=lon_min-2,llcrnrlat=lat_min-3,urcrnrlon=lon_max+2,urcrnrlat=lat_max+4.2, epsg=4326)

                            x, y = map(lon, lat)
                            cs=map.contourf(x,y,variable[:,:],cmap=plt.cm.jet,vmin=variable[:,:].min(), vmax=variable[:,:].max())
                            try:
                                map.arcgisimage(service='ESRI_Imagery_World_2D', xpixels = 1500, verbose= False)
                            except:
                                map.bluemarble()
                            cbar=map.colorbar(cs,location='bottom',pad="5%")
                            cbar.set_label(f'{variable_title}', fontsize=15)
                            if varb == 'thetao' or varb == 'bottomT':
                                plt.title('MODEL-PRODUCT [degrees_C]', fontsize=15)
                            else:
                                plt.title('MODEL-PRODUCT', fontsize=15)

                            plt.title('MODEL-PRODUCT', fontsize=20)
                            plt.show()

                        # case 2 : display the selected parameter on a map without a depth analysis
                        elif 2 < len(ds[varb].shape) < 4:

                            variable = ds.variables[varb][:]
                            try:
                                variable_title=ds[varb].attrs['standard_name']
                            except:
                                try:
                                    variable_title=ds[varb].attrs['long_name']
                                except:
                                    variable_title=varb
                            lon, lat = np.meshgrid(lons, lats)

                            plt.figure(figsize=(20,7))
                            plt.subplot(121)
                            if lon_min-2 <-180 or lat_min-3 < -90 or lon_max+2 > 180 or lat_max+4.2 >90:
                                map = Basemap(llcrnrlon=lon_min,llcrnrlat=lat_min,urcrnrlon=lon_max,urcrnrlat=lat_max, epsg=4326)
                            else:
                                map = Basemap(llcrnrlon=lon_min-2,llcrnrlat=lat_min-3,urcrnrlon=lon_max+2,urcrnrlat=lat_max+4.2, epsg=4326)

                            x, y = map(lon, lat)
                            cs=map.contourf(x,y,variable[0,:,:],cmap=plt.cm.jet,vmin=variable[0,:,:].min(), vmax=variable[0,:,:].max())

                            try:
                                map.arcgisimage(service='ESRI_Imagery_World_2D', xpixels = 1500, verbose= False)
                            except:
                                map.bluemarble()
                            cbar=map.colorbar(cs,location='bottom',pad="5%")
                            cbar.set_label(f'{variable_title}', fontsize=15)
                            if varb == 'thetao' or varb == 'bottomT':
                                plt.title('MODEL-PRODUCT [degrees_C]', fontsize=15)
                            else:
                                plt.title('MODEL-PRODUCT', fontsize=15)

                            plt.title('MODEL-PRODUCT', fontsize=20)
                            plt.show()

                        # case 3 : display the selected parameter on a map with a depth analysis
                        else: 

                            variable = ds.variables[varb][:]
                            try:
                                variable_title=ds[varb].attrs['standard_name']
                            except:
                                try:
                                    variable_title=ds[varb].attrs['long_name']
                                except:
                                    variable_title=varb
                            lon, lat = np.meshgrid(lons, lats)

                            plt.figure(figsize=(30,7))
                            plt.subplot(131)
                            if lon_min-2 <-180 or lat_min-3 < -90 or lon_max+2 > 180 or lat_max+4.2 >90:
                                map = Basemap(llcrnrlon=lon_min,llcrnrlat=lat_min,urcrnrlon=lon_max,urcrnrlat=lat_max, epsg=4326)
                            else:
                                map = Basemap(llcrnrlon=lon_min-2,llcrnrlat=lat_min-3,urcrnrlon=lon_max+2,urcrnrlat=lat_max+4.2, epsg=4326)
                            x, y = map(lon, lat)
                            cs=map.contourf(x,y,variable[0,0,:,:],cmap=plt.cm.jet,vmin=variable[0,0,:,:].min(), vmax=variable[0,0,:,:].max())
                            try:
                                map.arcgisimage(service='ESRI_Imagery_World_2D', xpixels = 1500, verbose= False)
                            except:
                                map.bluemarble()
                            cbar=map.colorbar(cs,location='bottom',pad="5%")
                            cbar.set_label(f'{variable_title}', fontsize=15)
                            if varb == 'thetao' or varb == 'bottomT':
                                plt.title('MODEL-PRODUCT (For Depth = 0) [degrees_C]', fontsize=15)
                            else:
                                plt.title('MODEL-PRODUCT (For Depth = 0)', fontsize=15)
                                
                            # add the display of the depth analysis 
                            plt.subplot(132)
                            # Get indexes for a Given Point (latitude = var_lat and longitude = var_lon)
                            if 'lon' in list(ds.variables):
                                if 'x' in list(ds.variables):
                                    vd=np.where(np.asarray(ds[varb]['x'])[:] == var_lon)
                                    vd2=np.where(np.asarray(ds[varb]['y'])[:] == var_lat)
                                    lons_test=ds[varb]['x'][np.asscalar(np.asarray(list(vd)))]
                                    lats_test=ds[varb]['y'][np.asscalar(np.asarray(list(vd2)))]
                                else:
                                    vd=np.where(np.asarray(ds[varb]['lon'])[:] == var_lon)
                                    vd2=np.where(np.asarray(ds[varb]['lat'])[:] == var_lat)
                                    lons_test=ds[varb]['lon'][np.asscalar(np.asarray(list(vd)))]
                                    lats_test=ds[varb]['lat'][np.asscalar(np.asarray(list(vd2)))]
                            elif 'longitude' in list(ds.variables):
                                if 'x' in list(ds.variables):
                                    vd=np.where(np.asarray(ds[varb]['x'])[:] == var_lon)
                                    vd2=np.where(np.asarray(ds[varb]['y'])[:] == var_lat)
                                    lons_test=ds[varb]['x'][np.asscalar(np.asarray(list(vd)))]
                                    lats_test=ds[varb]['y'][np.asscalar(np.asarray(list(vd2)))]
                                else:
                                    vd=np.where(np.asarray(ds[varb]['longitude'])[:] == var_lon)
                                    vd2=np.where(np.asarray(ds[varb]['latitude'])[:] == var_lat) 
                                    lons_test=ds[varb]['longitude'][np.asscalar(np.asarray(list(vd)))]
                                    lats_test=ds[varb]['latitude'][np.asscalar(np.asarray(list(vd2)))]
                            elif 'LONGITUDE' in list(ds.variables):
                                if 'x' in list(ds.variables):
                                    vd=np.where(np.asarray(ds[varb]['x'])[:] == var_lon)
                                    vd2=np.where(np.asarray(ds[varb]['y'])[:] == var_lat)
                                    lons_test=ds[varb]['x'][np.asscalar(np.asarray(list(vd)))]
                                    lats_test=ds[varb]['y'][np.asscalar(np.asarray(list(vd2)))]
                                else:
                                    vd=np.where(np.asarray(ds[varb]['LONGITUDE'])[:] == var_lon)
                                    vd2=np.where(np.asarray(ds[varb]['LATITUDE'])[:] == var_lat) 
                                    lons_test=ds[varb]['LONGITUDE'][np.asscalar(np.asarray(list(vd)))]
                                    lats_test=ds[varb]['LATITUDE'][np.asscalar(np.asarray(list(vd2)))]


                            indx_lat=np.asscalar(np.asarray(list(vd2)))
                            indx_lon=np.asscalar(np.asarray(list(vd)))


                            if lon_min-2 <-180 or lat_min-3 < -90 or lon_max+2 > 180 or lat_max+4.2 >90:
                                map = Basemap(llcrnrlon=lon_min,llcrnrlat=lat_min,urcrnrlon=lon_max,urcrnrlat=lat_max, epsg=4326)
                            else:
                                map = Basemap(llcrnrlon=lon_min-2,llcrnrlat=lat_min-3,urcrnrlon=lon_max+2,urcrnrlat=lat_max+4.2, epsg=4326)

                            s= 200*np.ones(1)
                            if math.isnan(np.array([ds[varb][0,0,indx_lat,indx_lon]])) == True:
                                cs3=map.scatter(np.array([lons_test]),np.array([lats_test]) , c=np.array([0]),s=s,cmap=plt.cm.gist_gray)
                            else:
                                cs3=map.scatter(np.array([lons_test]),np.array([lats_test]) , c=np.array([ds[varb][0,0,indx_lat,indx_lon]]),s=s,cmap=plt.cm.jet,vmin=variable[0,0,:,:].min(), vmax=variable[0,0,:,:].max())
                            try:
                                map.arcgisimage(service='ESRI_Imagery_World_2D', xpixels = 1500, verbose= False)
                            except:
                                map.bluemarble()
                            cbar3=map.colorbar(cs3,location='bottom',pad="5%")
                            cbar3.set_label(f'{variable_title}', fontsize=15)
                            plt.title(f'Selected Point', fontsize=20)

                            plt.subplot(133)
                            ds[varb][0,:,indx_lat,indx_lon].plot.line(y='depth',ylim=(110,0),yincrease=False)
                            plt.show()
                    except:
                        try:
                            varb=param_name
                            if len(ds[varb].shape) < 3:
                                ds[varb].plot()
                            elif 2 < len(ds[varb].shape) < 4:
                                ds[varb][0,:,:].plot()
                            else:
                                ds[varb][0,0,:,:].plot()
                        except:
                            print ("Displaying doesn't work, please choose another parameter or product (example : BALTICSEA_ANALYSIS_FORECAST_PHY_003_006) ") 
            # linking button and function together using a button's method
            button.on_click(on_button_clicked)
            # displaying button and its output together
            a=widgets.VBox([button,out])
            return(a)
        #----------------------------------------------------------------------------------------------------------------
        
        
        # display the interaction between the widgets 
        interact(random_function,
                 x = x_widget,
                 n = n_widget,
                 y = y_widget,
                z = z_widget);
        return(update_2)


###############################################################################################################
#--------------------------------------------------------------------------------------------
#       DISPLAY THE PARAMETERS OF THE FILE  (For SATELLITE PRODUCTS)
#--------------------------------------------------------------------------------------------
###############################################################################################################  
    @staticmethod
    def display_param_satellite(ds2,selected_list2,file_name2,scale_min,scale_max,scale):      
        ########## Initialize the widget ------------------------------------------------------------------
        x_widget = widgets.Dropdown(layout={'width': 'initial'},
            options=selected_list2,
            value=selected_list2[5],
            description='Parameters:',
            disabled=False)
        #-------------------------------------------------------------------------------------------------

        ## Define a function that updates the value of x_widget
        def update_3(*args):
            param_name=x_widget.value

        x_widget.observe(update_3)
        #-------------------------------------------------------------------------------------------------

        ####### configure the display according to the selected parameter
        def random_function(x):
            param_name=x
            if param_name == 'sea_surface_temperature' or param_name == 'adjusted_sea_surface_temperature':
                ds2 = xarray.open_dataset(file_name2)
                ds2[param_name][0,:,:]=ds2[param_name][0,:,:]-273.15
            else: 
                ds2 = xarray.open_dataset(file_name2)
                ds2[param_name]=ds2[param_name]

            button = widgets.Button(description='''Display The Param''')
            out = widgets.Output()
            # define the displaying button
            def on_button_clicked(_):
                  # "linking function with output"
                with out:
                    try: 
                        varb=param_name
                        # a condition to see if there is a variable that represents the depth in this parameter
                        if len(ds2[varb].shape) < 4:
                            # display the selected parameter on a map 
                            lons2 = ds2.variables['lon'][:]
                            lats2 = ds2.variables['lat'][:]
                            variable_ds2 = ds2.variables[varb][:]
                            variable_name = varb
                            lon2, lat2 = np.meshgrid(lons2, lats2)

                            plt.figure(figsize=(30,30))
                            plt.subplot(121)
                            map = Basemap(llcrnrlon=-40,llcrnrlat=20,urcrnrlon=60,urcrnrlat=70, epsg=4326)
                            x2, y2 = map(lon2, lat2)
                            if scale == 'Same_as_Model_Product':
                                cs2=map.contourf(x2,y2,variable_ds2[0,:,:],cmap=plt.cm.jet,vmin=scale_min, vmax=scale_max)
                            else:
                                cs2=map.contourf(x2,y2,variable_ds2[0,:,:],cmap=plt.cm.jet)
                            map.arcgisimage(service='ESRI_Imagery_World_2D', xpixels = 800, verbose= False)
                            cbar2=map.colorbar(cs2,location='bottom',pad="5%")
                            cbar2.set_label(f'{variable_name}', fontsize=15)
                            plt.title('SATELLITE OBSERVATION-PRODUCT', fontsize=20)
                            #--------------------------------------------------------

                            # display the selected parameter for a zoomed area of the image
                            plt.subplot(122)
                            map = Basemap(llcrnrlon=7,llcrnrlat=50,urcrnrlon=32,urcrnrlat=70, epsg=4326)
                            x2, y2 = map(lon2, lat2)
                            if scale == 'Same_as_Model_Product':
                                cs2=map.contourf(x2,y2,variable_ds2[0,:,:],cmap=plt.cm.jet,vmin=scale_min, vmax=scale_max)
                            else:
                                cs2=map.contourf(x2,y2,variable_ds2[0,:,:],cmap=plt.cm.jet)
                            map.arcgisimage(service='ESRI_Imagery_World_2D', xpixels = 1200, verbose= False)
                            cbar2=map.colorbar(cs2,location='bottom',pad="5%")
                            cbar2.set_label(f'{variable_name}', fontsize=15)
                            plt.title('SATELLITE OBSERVATION-PRODUCT', fontsize=20)
                            plt.show()
                            #------------------------------------------------------------------
                        else: 
                            # display the selected parameter on a map
                            lons2 = ds2.variables['lon'][:]
                            lats2 = ds2.variables['lat'][:]
                            variable_ds2 = ds2.variables[varb][:]
                            variable_name = varb
                            lon2, lat2 = np.meshgrid(lons2, lats2)
                            plt.figure(figsize=(30,30))
                            plt.subplot(121)
                            map = Basemap(llcrnrlon=-40,llcrnrlat=20,urcrnrlon=60,urcrnrlat=70, epsg=4326)
                            x2, y2 = map(lon2, lat2)
                            if scale == 'Same_as_Model_Product':
                                cs2=map.contourf(x2,y2,variable_ds2[0,0,:,:],cmap=plt.cm.jet,vmin=scale_min, vmax=scale_max)
                            else: 
                                cs2=map.contourf(x2,y2,variable_ds2[0,0,:,:],cmap=plt.cm.jet)
                            map.arcgisimage(service='ESRI_Imagery_World_2D', xpixels = 800, verbose= False)
                            cbar2=map.colorbar(cs2,location='bottom',pad="5%")
                            cbar2.set_label(f'{variable_name}', fontsize=15)
                            plt.title('SATELLITE OBSERVATION-PRODUCT', fontsize=20)
                            #------------------------------------------------------------------

                            # display the selected parameter for a zoomed area of the image
                            plt.subplot(122)
                            map = Basemap(llcrnrlon=7,llcrnrlat=50,urcrnrlon=32,urcrnrlat=70, epsg=4326)
                            x2, y2 = map(lon2, lat2)
                            if scale == 'Same_as_Model_Product':
                                cs2=map.contourf(x2,y2,variable_ds2[0,0,:,:],cmap=plt.cm.jet,vmin=scale_min, vmax=scale_max)
                            else:
                                cs2=map.contourf(x2,y2,variable_ds2[0,0,:,:],cmap=plt.cm.jet)
                            map.arcgisimage(service='ESRI_Imagery_World_2D', xpixels = 1200, verbose= False)
                            cbar2=map.colorbar(cs2,location='bottom',pad="5%")
                            cbar2.set_label(f'{variable_name}', fontsize=15)
                            plt.title('SATELLITE OBSERVATION-PRODUCT', fontsize=20)
                            plt.show()
                            #-----------------------------------------------------------------------------------
                    except:
                        print ("Displaying doesn't work, please choose another product (example : SST_EUR_SST_L3S_NRT_OBSERVATIONS_010_009_a) ") 



            # linking button and function together using a button's method
            button.on_click(on_button_clicked)
            # displaying button and its output together
            a=widgets.VBox([button,out])
            return(a)
            #----------------------------------------------------------------------------------------------------------------

        # display the interaction between the widget    
        interact(random_function,
                 x = x_widget);  
    

############################# INSITU PRODUCT ###########################################
########################################################################################

############################################################################################   
#--------------------------------------------------------------------------------------------
#                           DOWNLOAD THE FILES  
#--------------------------------------------------------------------------------------------
############################################################################################
    @staticmethod
    def Insitu_Products_download(host,user,password):
        # Get the list of all Insitu products offered by the cmems catalog
        data = {'In Situ NRT products': []}
        NRT_products = []
        #connect to CMEMS FTP
        with ftputil.FTPHost('nrt.cmems-du.eu', user, password) as ftp_host: 
            ftp_host.chdir('Core')
            product_list = ftp_host.listdir(ftp_host.curdir)
            for product in product_list:
                items = product.split('_')
                if 'INSITU' in items:
                    NRT_products.append(product)
        #------------------------------------------------------------------
        
        ########## Initialize the widgets ------------------------------------------------------------------
        x_widget = widgets.Dropdown(layout={'width': 'initial'},
            options=NRT_products,
            value=NRT_products[1],
            description='Product:',
            disabled=False)
        
        product_name=x_widget.value
        index_file = 'index_latest.txt' #type aimed index file  (index_latest - index_monthly - index_history )
        
        with ftputil.FTPHost(host, user, password) as ftp_host: 
                #open the index file to read
                with ftp_host.open("Core"+'/'+product_name+'/'+index_file, "r") as indexfile:
                    raw_index_info = pd.read_csv(indexfile, skiprows=5) #load it as pandas dataframe

        def flatten(items):
            """Yield items from any nested iterable"""
            for x in items:
                if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
                    for sub_x in flatten(x):
                        yield sub_x
                else:
                    yield x
        items=[]
        for i in range(len(raw_index_info.parameters)):
            items.append(raw_index_info.parameters[i].split(' '))
        items=list(flatten(items))
        items = list(set(items))


        y_widget = widgets.Dropdown(layout={'width': 'initial'},description='Parameter:')
        y_widget.options=items
        try:
            y_widget.value=items[items.index("TEMP")]
        except:
            y_widget.value=items[0]
            
        style = {'description_width': 'initial'}
        
        

        with ftputil.FTPHost(host, user, password) as ftp_host: 
            #open the index file to read
            with ftp_host.open("Core"+'/'+product_name+'/'+index_file, "r") as indexfile:
                raw_index_info = pd.read_csv(indexfile, skiprows=5) #load it as pandas dataframe
                
        z_widget = widgets.Text(layout={'width': 'initial'},value='2019-06-03T23:00:00Z',description=f'Enter an initial date between {raw_index_info.time_coverage_start[0]} and {raw_index_info.time_coverage_start[len(raw_index_info.time_coverage_start)-1]}  : ',style=style)

        w_widget = widgets.Text(layout={'width': 'initial'},value='2019-06-04T22:59:59Z',description=f'Enter an end date between {raw_index_info.time_coverage_end[0]} and {raw_index_info.time_coverage_end[len(raw_index_info.time_coverage_end)-1]}  : ',style=style)

        display(pd.DataFrame(data=data))
        #-----------------------------------------------------------------------------------------------------


        ####### Define a function that updates the content of (y_widget,w_widget,z_widget) based on what we select for x_widget
        def update4(*args):
            product_name=x_widget.value
            index_file = 'index_latest.txt' #type aimed index file  (index_latest - index_monthly - index_history )
            
            
            with ftputil.FTPHost(host, user, password) as ftp_host: 
                #open the index file to read
                with ftp_host.open("Core"+'/'+product_name+'/'+index_file, "r") as indexfile:
                    raw_index_info = pd.read_csv(indexfile, skiprows=5) #load it as pandas dataframe
                
            z_widget.description=f'Enter an initial date between {raw_index_info.time_coverage_start[0]} and {raw_index_info.time_coverage_start[len(raw_index_info.time_coverage_start)-1]}  : '
            w_widget.description=f'Enter an end date between {raw_index_info.time_coverage_end[0]} and {raw_index_info.time_coverage_end[len(raw_index_info.time_coverage_end)-1]}  : '

            with ftputil.FTPHost(host, user, password) as ftp_host: 
                #open the index file to read
                with ftp_host.open("Core"+'/'+product_name+'/'+index_file, "r") as indexfile:
                    raw_index_info = pd.read_csv(indexfile, skiprows=5) #load it as pandas dataframe

            def flatten(items):
                """Yield items from any nested iterable"""
                for x in items:
                    if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
                        for sub_x in flatten(x):
                            yield sub_x
                    else:
                        yield x
            items=[]
            for i in range(len(raw_index_info.parameters)):
                items.append(raw_index_info.parameters[i].split(' '))
            items=list(flatten(items))
            items = list(set(items))

            y_widget.options=items
            try:
                y_widget.value=items[items.index("TEMP")]
            except:
                y_widget.value=items[0]
            z_widget.value='2019-06-03T23:00:00Z'
            w_widget.value='2019-06-04T22:59:59Z'
            
            return(x_widget.value,y_widget.value)

        x_widget.observe(update4,'value')
        y_widget.observe(update4,'value')
        #---------------------------------------------------------------------------------------------------------------



        ######## Define the download procedure using the ftp protocol
        def random_function(x, y, z, w):
            product_name=x
            aimed_parameter=y
            date_format = "%Y-%m-%dT%H:%M:%SZ" 
            ini = datetime.datetime.strptime(z, date_format)
            end = datetime.datetime.strptime(w, date_format)
            
            # define the downloading button
            button = widgets.Button(description='''Download The Files''')
            out = widgets.Output()
            def on_button_clicked(_):
              # "linking function with output"
              with out:
                # set the output_directory of the files
                if os.getcwd() == '/home/jovyan/public':
                    output_directory='/home/jovyan/work'+'/cmems_data/03_Insitu_product'
                else:
                    output_directory=os.getcwd()+'/cmems_data/03_Insitu_product'
                #-------------------------------------------------------
                
                # creating a folder using the output_directory    
                p = Path(output_directory)
                p.mkdir(parents=True, exist_ok=True)
                
                ####### downloading the files using the ftp protocol
                print(f'Downloading The Files in {output_directory}')
                # connect to CMEMS FTP
                dataset_all=[]
                with ftputil.FTPHost(host, user, password) as ftp_host: 

                    # open the index file to read
                    with ftp_host.open("Core"+'/'+product_name+'/'+index_file, "r") as indexfile:

                        # read the index file as a comma-separate-value file
                        index = np.genfromtxt(indexfile, skip_header=6, unpack=False, delimiter=',', dtype=None, names=['catalog_id', 'file_name','geospatial_lat_min', 'geospatial_lat_max', 'geospatial_lon_min','geospatial_lon_max','time_coverage_start', 'time_coverage_end', 'provider', 'date_update', 'data_mode', 'parameters'])

                        # loop over the lines/netCDFs and download the most sutable ones for you
                        for netCDF in index:

                            # getting ftplink, filepath and filename
                            ftplink = netCDF['file_name'].decode('utf-8')
                            filepath = '/'.join(ftplink.split('/')[3:len(ftplink.split('/'))])
                            ncdf_file_name = ftplink[ftplink.rfind('/')+1:]

                            # download netCDF if meeting selection criteria
                            parameters = netCDF['parameters'].decode('utf-8')
                            time_start = datetime.datetime.strptime(netCDF['time_coverage_start'].decode('utf-8'), date_format)
                            time_end = datetime.datetime.strptime(netCDF['time_coverage_start'].decode('utf-8'), date_format)
                            if aimed_parameter in parameters and time_start > ini  and time_end < end: 
                                if ftp_host.path.isfile(filepath):
                                    cwd = os.getcwd()
                                    os.chdir(output_directory)
                                    ftp_host.download(filepath, ncdf_file_name)  # remote, local
                                    dataset_all.append(ncdf_file_name)
                                    os.chdir(cwd)
                
                # create a text file using the output directory containing all the names of downloaded netcdf files  
                with open(output_directory+'/Datasets_downloaded.txt', 'w') as filehandle:  
                    for listitem in dataset_all:
                        filehandle.write('%s\n' % listitem)

                if dataset_all == []:
                    print("No files were downloaded, please check that the chosen date is wide enough and that it is between the time range indicated at the top")        
                else:
                    print('Done')
                    
                return(dataset_all)  
                #------------------------------------------------------------
            # linking button and function together using a button's method
            button.on_click(on_button_clicked)
            # displaying button and its output together
            aa=widgets.VBox([button,out])
            display(aa)


        # display the interaction between the widgets 
        interact(random_function,
                 x = x_widget,
                 y = y_widget,
                 z = z_widget,
                 w = w_widget);
        
        return(update4)
    
    
#############################################################################################
#--------------------------------------------------------------------------------------------
#                       READ THE DOWNLOADED THE FILES  
#--------------------------------------------------------------------------------------------
#############################################################################################  
    @staticmethod
    def Insitu_read_files(dataset_all):
        # get the current directory of the files 
        if os.getcwd() == '/home/jovyan/public':
            output_directory='/home/jovyan/work'+'/cmems_data/03_Insitu_product'
        else:
            output_directory=os.getcwd()+'/cmems_data/03_Insitu_product'
            
        # reading the netcdf files     
        All_ds=[]
        for i in range(len(dataset_all)):
            vars()[f'ds_{i+1}'] = xarray.open_dataset(output_directory+f'/{dataset_all[i]}')      
            All_ds.append(vars()[f'ds_{i+1}'])
        return(All_ds)
    
#############################################################################################  
#--------------------------------------------------------------------------------------------
#                DISPLAY THE PARAMTERS OF THE DOWNLOADED THE FILES  
#--------------------------------------------------------------------------------------------    
#############################################################################################
    @staticmethod
    def display_Insitu_product(All_ds,selected_product,param,scale_min,scale_max,scale):
        try:
            if selected_product == 'INSITU_BAL_NRT_OBSERVATIONS_013_032': 
                # get the values of the selected parameter at the surface (depth=0) for all the netcdfs files
                var_temp_test2=[]
                for i in range(len(All_ds)):
                    if All_ds[i][param][0].size > 1:
                        var_temp_test=All_ds[i][param][0,0]
                        var_temp_test2.append(var_temp_test)
                    else:
                        var_temp_test=All_ds[i][param][0]
                        var_temp_test2.append(var_temp_test)
                var_temp_test2=np.asarray(var_temp_test2, dtype=np.float)[:]
                #--------------------------------------------------------------------------------------------

                # get the values of the latitude of the selected parameter on the surface (depth = 0) for all netcdf files
                lats_test2=[]
                for i in range(len(All_ds)):
                    lats_test=All_ds[i]['LATITUDE'][0]
                    lats_test2.append(lats_test)
                lats_test2=np.asarray(lats_test2, dtype=np.float)[:]
                #--------------------------------------------------------------------------------------------------------

                # get the values of the longitude of the selected parameter on the surface (depth = 0) for all netcdf files
                lons_test2=[]
                for i in range(len(All_ds)):
                    lons_test=All_ds[i]['LONGITUDE'][0]
                    lons_test2.append(lons_test)
                lons_test2=np.asarray(lons_test2, dtype=np.float)[:]
                #----------------------------------------------------------------------------------------------------------

                # display the selected points (of all netcdf files at depth=0) on a map
                plt.figure(figsize=(20,7))
                map = Basemap(llcrnrlon=7,llcrnrlat=50,urcrnrlon=32,urcrnrlat=70, epsg=4326)
                s= 200*np.ones(len(All_ds))
                if scale == 'Same_as_Model_Product':
                    cs3=map.scatter(lons_test2,lats_test2 , c=var_temp_test2,s=s,cmap=plt.cm.jet,vmin=scale_min, vmax=scale_max)
                else:
                    cs3=map.scatter(lons_test2,lats_test2 , c=var_temp_test2,s=s,cmap=plt.cm.jet)
                map.arcgisimage(service='ESRI_Imagery_World_2D', xpixels = 1500, verbose= False)
                cbar3=map.colorbar(cs3,location='bottom',pad="5%")
                cbar3.set_label('Temperature', fontsize=15)
                plt.title('IN-SITU-PRODUCT', fontsize=20)
                plt.show()

                # get the list of indexes of the files that permit a depth analysis 
                ii=[]
                for i in range(len(All_ds)):
                    if All_ds[i]['TEMP'][0].size > 1:
                        ii.append(i)

                remove_index=[]        
                for j in ii:
                    if All_ds[j]['TEMP'][0].size > 1 and np.isnan(All_ds[j]['TEMP'][0,:]).any() == True: 
                        remove_index.append(ii.index(j))
                ii=list(np.delete(ii,remove_index))
                #-------------------------------------------------------------------

                # get the values of the selected parameter at the surface (depth=0) for the files that permit a depth analysis
                var_temp_test2=[]
                for i in ii:
                    var_temp_test=All_ds[i][param][0,0]
                    var_temp_test2.append(var_temp_test)
                var_temp_test2=np.asarray(var_temp_test2, dtype=np.float)[:]
                #------------------------------------------------------------------------------------------------------------

                # get the values of the latitude of the selected parameter on the surface (depth = 0) for the files that permit a depth analysis
                lats_test2=[]
                for i in ii:
                    lats_test=All_ds[i]['LATITUDE'][0]
                    lats_test2.append(lats_test)
                lats_test2=np.asarray(lats_test2, dtype=np.float)[:]
                #------------------------------------------------------------------------------------------------------------

                # get the values of the latitude of the selected parameter on the surface (depth = 0) for the files that permit a depth analysis
                lons_test2=[]
                for i in ii:
                    lons_test=All_ds[i]['LONGITUDE'][0]
                    lons_test2.append(lons_test)
                lons_test2=np.asarray(lons_test2, dtype=np.float)[:]
                #------------------------------------------------------------------------------------------------------------

                # display the selected points (for the files that permit a depth analysis at depth=0) on a map
                fig = plt.figure(figsize=(22,30))
                for k in range(len(ii)):
                    ax = fig.add_subplot(5,4,k+1)
                    map = Basemap(llcrnrlon=7,llcrnrlat=50,urcrnrlon=32,urcrnrlat=70, epsg=4326)
                    s= 200*np.ones(1)
                    if scale == 'Same_as_Model_Product':
                        cs3=map.scatter(np.array([lons_test2[k]]),np.array([lats_test2[k]]) , c=np.array([var_temp_test2[k]]),s=s,cmap=plt.cm.jet,vmin=scale_min, vmax=scale_max)
                    else:
                        cs3=map.scatter(np.array([lons_test2[k]]),np.array([lats_test2[k]]) , c=np.array([var_temp_test2[k]]),s=s,cmap=plt.cm.jet)
                    map.arcgisimage(service='ESRI_Imagery_World_2D', xpixels = 1500, verbose= False)
                    cbar3=map.colorbar(cs3,location='bottom',pad="5%")
                    cbar3.set_label('Temperature', fontsize=15)
                    plt.title(f'IN-SITU-PRODUCT (LONGITUDE = {round(lons_test2[k],2)}, LATITUDE = {round(lats_test2[k],2)})', fontsize=12)
                    fig.tight_layout()
                    fig.subplots_adjust(top=0.95)
                plt.show()


                # display a depth analysis figure of the selected points 
                if len(ii) < 4:
                    fig = plt.figure(figsize=(18,24))
                else:
                    fig = plt.figure(figsize=(22,24))
                for j,num in zip(ii, range(1,len(ii)+1)):
                    if len(ii) < 4:
                        ax = fig.add_subplot(5,len(ii),num)
                    else:
                        ax = fig.add_subplot(5,4,num)
                    All_ds[j]['TEMP'][0,:].plot.line(y='DEPTH',ylim=(All_ds[j]['DEPTH'].max(),All_ds[j]['DEPTH'].min()),yincrease=False,ax=ax)
                    ax2 = ax.twinx()
                    lat_graph=np.asscalar(np.asarray(All_ds[j]['LATITUDE'][0]))
                    lon_graph=np.asscalar(np.asarray(All_ds[j]['LONGITUDE'][0]))
                    plt.ylabel(f'LONGITUDE = {round(lon_graph,2)}       LATITUDE = {round(lat_graph,2)} ', fontsize=14)
                    fig.suptitle("IN-SITU-PRODUCT", fontsize=25)
                    fig.tight_layout()
                    fig.subplots_adjust(top=0.95)
                plt.show()
            else:
                print ("Displaying doesn't work, please choose another product (example : INSITU_BAL_NRT_OBSERVATIONS_013_032) ") 

        except:
            print ("Displaying doesn't work, please choose another product (example : INSITU_BAL_NRT_OBSERVATIONS_013_032) ")
        
    
#############################################################################################
#--------------------------------------------------------------------------------------------
#                       DISPLAY ALL THE RESULTS TOGETHER
#--------------------------------------------------------------------------------------------     
############################################################################################# 
    @staticmethod
    def Display_all_figures(ds,param_model_product,ds2,param_satellite_product,file_name2,All_ds,param_insitu,img,img_sentinel2,img_radar,scale_min,scale_max,scale):
        plt.figure(figsize=(40,50))

        plt.subplot(131)
        varb=param_model_product
        if len(ds[varb].shape) < 4:
            # define the longitude (max,min) and latitude (max,min) for the displaying 
            lon_max=ds.variables['lon'][:].max()
            lon_min=ds.variables['lon'][:].min()
            lat_max=ds.variables['lat'][:].max()
            lat_min=ds.variables['lat'][:].min()
            lon_max=np.asscalar(np.asarray(lon_max, dtype=np.float))
            lon_min=np.asscalar(np.asarray(lon_min, dtype=np.float))
            lat_max=np.asscalar(np.asarray(lat_max, dtype=np.float))
            lat_min=np.asscalar(np.asarray(lat_min, dtype=np.float))
            #-------------------------------------------------------------------------

            # display the selected parameter on a map 
            # case1 : the parameter has no depth variable
            lons = ds.variables['lon'][:]
            lats = ds.variables['lat'][:]
            variable = ds.variables[varb][:]
            variable_title=ds[varb].attrs['standard_name']
            lon, lat = np.meshgrid(lons, lats)
            map = Basemap(llcrnrlon=7,llcrnrlat=50,urcrnrlon=32,urcrnrlat=70, epsg=4326)
            x, y = map(lon, lat)
            if scale == 'Same_as_Model_Product':
                cs=map.contourf(x,y,variable[0,:,:],cmap=plt.cm.jet,vmin=scale_min, vmax=scale_max)
            else:
                cs=map.contourf(x,y,variable[0,:,:],cmap=plt.cm.jet) #,vmin=-3.15, vmax=6.85)
            map.arcgisimage(service='ESRI_Imagery_World_2D', xpixels = 1500, verbose= False)
            cbar=map.colorbar(cs,location='bottom',pad="5%")
            cbar.set_label(f'{variable_title}', fontsize=15)
            plt.title('MODEL-PRODUCT', fontsize=20)
            #-------------------------------------------------------------------------
        else: 
            # define the longitude (max,min) and latitude (max,min) for the displaying 
            lon_max=ds.variables['lon'][:].max()
            lon_min=ds.variables['lon'][:].min()
            lat_max=ds.variables['lat'][:].max()
            lat_min=ds.variables['lat'][:].min()
            lon_max=np.asscalar(np.asarray(lon_max, dtype=np.float))
            lon_min=np.asscalar(np.asarray(lon_min, dtype=np.float))
            lat_max=np.asscalar(np.asarray(lat_max, dtype=np.float))
            lat_min=np.asscalar(np.asarray(lat_min, dtype=np.float))
            #-------------------------------------------------------------------------
            
            # display the selected parameter on a map 
            # case2 : the parameter has a depth variable
            lons = ds.variables['lon'][:]
            lats = ds.variables['lat'][:]
            variable = ds.variables[varb][:]
            variable_title=ds[varb].attrs['standard_name']
            lon, lat = np.meshgrid(lons, lats)
            map = Basemap(llcrnrlon=7,llcrnrlat=50,urcrnrlon=32,urcrnrlat=70, epsg=4326)
            x, y = map(lon, lat)
            if scale == 'Same_as_Model_Product':
                cs=map.contourf(x,y,variable[0,0,:,:],cmap=plt.cm.jet,vmin=scale_min, vmax=scale_max)
            else:
                cs=map.contourf(x,y,variable[0,0,:,:],cmap=plt.cm.jet) #,vmin=-3.15, vmax=6.85)
            map.arcgisimage(service='ESRI_Imagery_World_2D', xpixels = 1500, verbose= False)
            cbar=map.colorbar(cs,location='bottom',pad="5%")
            cbar.set_label(f'{variable_title}', fontsize=15)
            plt.title('MODEL-PRODUCT', fontsize=20)
            #-------------------------------------------------------------------------

        plt.subplot(132)
        # configure the display according to the selected parameter
        varb2=param_satellite_product
        if param_satellite_product == 'sea_surface_temperature' or param_satellite_product =='adjusted_sea_surface_temperature':
            ds2 = xarray.open_dataset(file_name2)
            ds2[param_satellite_product][0,:,:]=ds2[param_satellite_product][0,:,:]-273.15
        else: 
            ds2[param_satellite_product]=ds2[param_satellite_product]

        if len(ds2[varb2].shape) < 4:
            # display the selected parameter on a map
            # case1 : the parameter has no depth variable
            lons2 = ds2.variables['lon'][:]
            lats2 = ds2.variables['lat'][:]
            variable_ds2 = ds2.variables[varb2][:]
            variable_name = varb2
            lon2, lat2 = np.meshgrid(lons2, lats2)
            map = Basemap(llcrnrlon=7,llcrnrlat=50,urcrnrlon=32,urcrnrlat=70, epsg=4326)
            x2, y2 = map(lon2, lat2)
            if scale == 'Same_as_Model_Product':
                cs2=map.contourf(x2,y2,variable_ds2[0,:,:],cmap=plt.cm.jet,vmin=scale_min, vmax=scale_max)
            else:
                cs2=map.contourf(x2,y2,variable_ds2[0,:,:],cmap=plt.cm.jet)
            map.arcgisimage(service='ESRI_Imagery_World_2D', xpixels = 1500, verbose= False)
            cbar2=map.colorbar(cs2,location='bottom',pad="5%")
            cbar2.set_label(f'{variable_name}', fontsize=15)
            plt.title('SATELLITE OBSERVATION-PRODUCT', fontsize=20)
            #------------------------------------------------------------------
        else: 
            
            # display the selected parameter on a map
            # case2 : the parameter has a depth variable
            lons2 = ds2.variables['lon'][:]
            lats2 = ds2.variables['lat'][:]
            variable_ds2 = ds2.variables[varb2][:]
            variable_name = varb2
            lon2, lat2 = np.meshgrid(lons2, lats2)
            map = Basemap(llcrnrlon=7,llcrnrlat=50,urcrnrlon=32,urcrnrlat=70, epsg=4326)
            x2, y2 = map(lon2, lat2)
            if scale == 'Same_as_Model_Product':
                cs2=map.contourf(x2,y2,variable_ds2[0,0,:,:],cmap=plt.cm.jet,vmin=scale_min, vmax=scale_max)
            else:
                cs2=map.contourf(x2,y2,variable_ds2[0,0,:,:],cmap=plt.cm.jet)
            map.arcgisimage(service='ESRI_Imagery_World_2D', xpixels = 1500, verbose= False)
            cbar2=map.colorbar(cs2,location='bottom',pad="5%")
            cbar2.set_label(f'{variable_name}', fontsize=15)
            plt.title('SATELLITE OBSERVATION-PRODUCT', fontsize=20)
            #-------------------------------------------------------------------------------

        plt.subplot(133)
        
        # get the values of the selected parameter at the surface (depth=0) for all the netcdfs files
        var_temp_test2=[]
        for i in range(len(All_ds)):
            if All_ds[i][param_insitu][0].size > 1:
                var_temp_test=All_ds[i][param_insitu][0,0]
                var_temp_test2.append(var_temp_test)
            else:
                var_temp_test=All_ds[i][param_insitu][0]
                var_temp_test2.append(var_temp_test)
        var_temp_test2=np.asarray(var_temp_test2, dtype=np.float)[:]
        #---------------------------------------------------------------------------------------------
        
        # get the values of the latitude of the selected parameter on the surface (depth = 0) for all netcdf files
        lats_test2=[]
        for i in range(len(All_ds)):
            lats_test=All_ds[i]['LATITUDE'][0]
            lats_test2.append(lats_test)
        lats_test2=np.asarray(lats_test2, dtype=np.float)[:]
        #----------------------------------------------------------------------------------------------------------
        
        # get the values of the longitude of the selected parameter on the surface (depth = 0) for all netcdf files
        lons_test2=[]
        for i in range(len(All_ds)):
            lons_test=All_ds[i]['LONGITUDE'][0]
            lons_test2.append(lons_test)
        lons_test2=np.asarray(lons_test2, dtype=np.float)[:]
        #----------------------------------------------------------------------------------------------------------


        # display the selected points (of all netcdf files at depth=0) on a map
        map = Basemap(llcrnrlon=7,llcrnrlat=50,urcrnrlon=32,urcrnrlat=70, epsg=4326)
        s= 200*np.ones(len(All_ds))
        if scale == 'Same_as_Model_Product':
            cs3=map.scatter(lons_test2,lats_test2 , c=var_temp_test2,s=s,cmap=plt.cm.jet,vmin=scale_min, vmax=scale_max)
        else:
            cs3=map.scatter(lons_test2,lats_test2 , c=var_temp_test2,s=s,cmap=plt.cm.jet)
        map.arcgisimage(service='ESRI_Imagery_World_2D', xpixels = 1500, verbose= False)
        cbar3=map.colorbar(cs3,location='bottom',pad="5%")
        cbar3.set_label('Temperature', fontsize=15)
        plt.title('IN-SITU-PRODUCT', fontsize=20)
        #----------------------------------------------------------------------------------------------------------


        # display the Sentinel-2 cloudless image for 2018 by EOX, Sentinel 1 image and Sentinel 2 image 
        plt.figure(figsize=(40,50))
        plt.subplot(131)
        map = Basemap(llcrnrlon=7.041666030883789,llcrnrlat=50.024993896484375,urcrnrlon=32.3194465637207,urcrnrlat=70.09166259765625, epsg=4326)
        
        varb=param_model_product
        if len(ds[varb].shape) < 4:
            if scale == 'Same_as_Model_Product':
                cs=map.contourf(x,y,variable[0,:,:],cmap=plt.cm.jet,vmin=scale_min, vmax=scale_max)
            else:
                cs=map.contourf(x,y,variable[0,:,:],cmap=plt.cm.jet) 
        else:
            if scale == 'Same_as_Model_Product':
                cs=map.contourf(x,y,variable[0,0,:,:],cmap=plt.cm.jet,vmin=scale_min, vmax=scale_max)
            else:
                cs=map.contourf(x,y,variable[0,0,:,:],cmap=plt.cm.jet)            
        map.imshow(Image.open(img),origin='upper')
        plt.title('Sentinel-2 cloudless image for 2018 by EOX', fontsize=20)

        plt.subplot(132)
        map = Basemap(llcrnrlon=7.041666030883789,llcrnrlat=50.024993896484375,urcrnrlon=32.3194465637207,urcrnrlat=70.09166259765625, epsg=4326)
        if len(ds[varb].shape) < 4:
            if scale == 'Same_as_Model_Product':
                cs=map.contourf(x,y,variable[0,:,:],cmap=plt.cm.jet,vmin=scale_min, vmax=scale_max)
            else:
                cs=map.contourf(x,y,variable[0,:,:],cmap=plt.cm.jet) 
        else:
            if scale == 'Same_as_Model_Product':
                cs=map.contourf(x,y,variable[0,0,:,:],cmap=plt.cm.jet,vmin=scale_min, vmax=scale_max)
            else:
                cs=map.contourf(x,y,variable[0,0,:,:],cmap=plt.cm.jet)           
        map.imshow(img_sentinel2,origin='upper')
        plt.title('Sentinel-2 image', fontsize=20)

        plt.subplot(133)
        map = Basemap(llcrnrlon=7.041666030883789,llcrnrlat=50.024993896484375,urcrnrlon=32.3194465637207,urcrnrlat=70.09166259765625, epsg=4326)
        if len(ds[varb].shape) < 4:
            if scale == 'Same_as_Model_Product':
                cs=map.contourf(x,y,variable[0,:,:],cmap=plt.cm.jet,vmin=scale_min, vmax=scale_max)
            else:
                cs=map.contourf(x,y,variable[0,:,:],cmap=plt.cm.jet) 
        else:
            if scale == 'Same_as_Model_Product':
                cs=map.contourf(x,y,variable[0,0,:,:],cmap=plt.cm.jet,vmin=scale_min, vmax=scale_max)
            else:
                cs=map.contourf(x,y,variable[0,0,:,:],cmap=plt.cm.jet)         
        
        map.imshow(img_radar,cmap='gray',origin='upper')
        plt.title('Sentinel-1 image', fontsize=20)

        # get the list of indexes of the files that permit a depth analysis (insitu product)
        ii=[]
        for i in range(len(All_ds)):
            if All_ds[i]['TEMP'][0].size > 1:
                ii.append(i)
        remove_index=[]        
        for j in ii:
            if All_ds[j][param_insitu][0].size > 1 and np.isnan(All_ds[j][param_insitu][0,:]).any() == True: 
                remove_index.append(ii.index(j))
        ii=list(np.delete(ii,remove_index))
        
        # get the values of the selected parameter at the surface (depth=0) for the files that permit a depth analysis
        var_temp_test2=[]
        for i in ii:
            var_temp_test=All_ds[i][param_insitu][0,0]
            var_temp_test2.append(var_temp_test)
        var_temp_test2=np.asarray(var_temp_test2, dtype=np.float)[:]
        #------------------------------------------------------------------------------------------------------------

        # get the values of the latitude of the selected parameter on the surface (depth = 0) for the files that permit a depth analysis
        lats_test2=[]
        for i in ii:
            lats_test=All_ds[i]['LATITUDE'][0]
            lats_test2.append(lats_test)
        lats_test2=np.asarray(lats_test2, dtype=np.float)[:]
        #------------------------------------------------------------------------------------------------------------

        # get the values of the latitude of the selected parameter on the surface (depth = 0) for the files that permit a depth analysis
        lons_test2=[]
        for i in ii:
            lons_test=All_ds[i]['LONGITUDE'][0]
            lons_test2.append(lons_test)
        lons_test2=np.asarray(lons_test2, dtype=np.float)[:]

        # display the selected points (for the files that permit a depth analysis at depth=0) on a map
        fig = plt.figure(figsize=(22,30))
        for k in range(len(ii)):
            ax = fig.add_subplot(5,4,k+1)
            map = Basemap(llcrnrlon=7,llcrnrlat=50,urcrnrlon=32,urcrnrlat=70, epsg=4326)
            s= 200*np.ones(1)
            if scale == 'Same_as_Model_Product':
                cs3=map.scatter(np.array([lons_test2[k]]),np.array([lats_test2[k]]) , c=np.array([var_temp_test2[k]]),s=s,cmap=plt.cm.jet,vmin=scale_min, vmax=scale_max)
            else:
                cs3=map.scatter(np.array([lons_test2[k]]),np.array([lats_test2[k]]) , c=np.array([var_temp_test2[k]]),s=s,cmap=plt.cm.jet)
            map.arcgisimage(service='ESRI_Imagery_World_2D', xpixels = 500, verbose= False)
            cbar3=map.colorbar(cs3,location='bottom',pad="5%")
            cbar3.set_label('Temperature', fontsize=15)
            plt.title(f'IN-SITU-PRODUCT (LONGITUDE = {round(lons_test2[k],2)}, LATITUDE = {round(lats_test2[k],2)})', fontsize=12)
            fig.tight_layout()
            fig.subplots_adjust(top=0.95)
        plt.show()
        
        # display a depth analysis figure of the selected points (insitu product)
        if len(ii) < 4:
            fig = plt.figure(figsize=(18,24))
        else:
            fig = plt.figure(figsize=(22,24))
        for j,num in zip(ii, range(1,len(ii)+1)):
            if len(ii) < 4:
                ax = fig.add_subplot(5,len(ii),num)
            else:
                ax = fig.add_subplot(5,4,num)
            All_ds[j][param_insitu][0,:].plot.line(y='DEPTH',ylim=(All_ds[j]['DEPTH'].max(),All_ds[j]['DEPTH'].min()),yincrease=False,ax=ax)
            ax2 = ax.twinx()
            lat_graph=np.asscalar(np.asarray(All_ds[j]['LATITUDE'][0]))
            lon_graph=np.asscalar(np.asarray(All_ds[j]['LONGITUDE'][0]))
            plt.ylabel(f'LONGITUDE = {round(lon_graph,2)}       LATITUDE = {round(lat_graph,2)} ', fontsize=14)
            fig.suptitle("IN-SITU-PRODUCT", fontsize=25)
            fig.tight_layout()
            fig.subplots_adjust(top=0.95)
        plt.show()
        #-----------------------------------------------------------------------------------
        if len(ii) < 4:
            fig = plt.figure(figsize=(18,24))
        else:
            fig = plt.figure(figsize=(22,24))
        for j,num in zip(ii, range(1,len(ii)+1)):
            lat_graph=np.asscalar(np.asarray(All_ds[j]['LATITUDE'][0]))
            lon_graph=np.asscalar(np.asarray(All_ds[j]['LONGITUDE'][0]))
            vd=np.where(np.asarray(ds[varb]['lat'], dtype=np.float)[:].round(1) == round(lat_graph,1))
            vd2=np.where(np.asarray(ds[varb]['lon'], dtype=np.float)[:].round(1) == round(lon_graph,1))
            indx_lat=(list(vd[0]))
            indx_lon=list(vd2[0])
            ds[varb][0,:,indx_lat[0],indx_lon[0]].plot.line(y='depth',ylim=(All_ds[j]['DEPTH'].max(),All_ds[j]['DEPTH'].min()),yincrease=False)
            fig.suptitle("MODEL-PRODUCT", fontsize=25)
            fig.tight_layout()
            fig.subplots_adjust(top=0.95)
        plt.show()
        #-----------------------------------------------------------------------------------------------
                    

#############################################################################################                
#--------------------------------------------------------------------------------------------
#                  DISPLAY ALL THE RESULTS ON AN INTERACTIVE MAP
#--------------------------------------------------------------------------------------------         
#############################################################################################
    @staticmethod
    def Display_all_figures_folium(wms_Sentinel2,Sentinel2_layer,wms_Sentinel1,Sentinel1_layer,ds,param_model_product,ds2,param_satellite_product,file_name2,img_sentinel2,img_radar,scale_min,scale_max,scale,All_ds,param):
        # set the output directory of the html file
        if os.getcwd() == '/home/jovyan/public':
            output_directory='/home/jovyan/work/cmems_data'
        else:
            output_directory=os.getcwd()+'/cmems_data'
        print(f'Creating the file "folium_map.html" in {output_directory}')
        

        varb=param_model_product
        if len(ds[varb].shape) < 4:
            # create a geojson file that contain the display of the selected parameter (model product) on a map
            # case1 : the parameter has no depth variable
            lons = ds.variables['lon'][:]
            lats = ds.variables['lat'][:]
            variable = ds.variables[varb][:]
            variable_title=ds[varb].attrs['standard_name']
            lon, lat = np.meshgrid(lons, lats)
            map = Basemap(llcrnrlon=7,llcrnrlat=50,urcrnrlon=32,urcrnrlat=70, epsg=4326)
            x, y = map(lon, lat)
            fig = plt.figure()
            contourf = plt.contourf(x,y,variable[0,:,:],cmap=plt.cm.jet,vmin=-3.15, vmax=6.85);
            geojson = geojsoncontour.contourf_to_geojson(
                contourf=contourf,
                min_angle_deg=3.0,
                ndigits=5,
                stroke_width=1,
                fill_opacity=10)
            plt.close(fig)
        else:
            # create a geojson file that contain the display of the selected parameter (model product) on a map
            # case2 : the parameter has a depth variable
            lons = ds.variables['lon'][:]
            lats = ds.variables['lat'][:]
            variable = ds.variables[varb][:]
            variable_title=ds[varb].attrs['standard_name']
            lon, lat = np.meshgrid(lons, lats)
            map = Basemap(llcrnrlon=7,llcrnrlat=50,urcrnrlon=32,urcrnrlat=70, epsg=4326)
            x, y = map(lon, lat)
            fig = plt.figure()
            if scale == 'Same_as_Model_Product':
                contourf = plt.contourf(x,y,variable[0,0,:,:],cmap=plt.cm.jet,vmin=scale_min, vmax=scale_max);
            else:
                contourf = plt.contourf(x,y,variable[0,0,:,:],cmap=plt.cm.jet);
            geojson = geojsoncontour.contourf_to_geojson(
                contourf=contourf,
                min_angle_deg=3.0,
                ndigits=5,
                stroke_width=1,
                fill_opacity=10)
            plt.close(fig)
            #---------------------------------------------------------------------------------


        # configure the display according to the selected parameter
        varb2=param_satellite_product
        if param_satellite_product == 'sea_surface_temperature' or param_satellite_product == 'adjusted_sea_surface_temperature':
            ds2 = xarray.open_dataset(file_name2)
            ds2[param_satellite_product][0,:,:]=ds2[param_satellite_product][0,:,:]-273.15
        else: 
            ds2[param_satellite_product]=ds2[param_satellite_product]
        #-------------------------------------------------------------
        
        if len(ds2[varb2].shape) < 4:
            # create a geojson file that contain the display of the selected parameter (satellite product) on a map
            # case1 : the parameter has no depth variable
            lons2 = ds2.variables['lon'][:]
            lats2 = ds2.variables['lat'][:]
            variable_ds2 = ds2.variables[varb2][:]
            lon2, lat2 = np.meshgrid(lons2, lats2)
            map = Basemap(llcrnrlon=7,llcrnrlat=50,urcrnrlon=32,urcrnrlat=70, epsg=4326)
            x2, y2 = map(lon2, lat2)
            np.seterr(divide='ignore', invalid='ignore')
            fig = plt.figure()
            if scale == 'Same_as_Model_Product':
                contourf_ds2 = plt.contourf(x2,y2,variable_ds2[0,:,:],cmap=plt.cm.jet,vmin=scale_min, vmax=scale_max);
            else:
                contourf_ds2 = plt.contourf(x2,y2,variable_ds2[0,:,:],cmap=plt.cm.jet);
            geojson_ds2 = geojsoncontour.contourf_to_geojson(
                contourf=contourf_ds2,
                min_angle_deg=3.0,
                ndigits=5,
                stroke_width=1,
                fill_opacity=1)
            plt.close(fig)
            #-----------------------------------------------------------------------------------
        else: 
            # create a geojson file that contain the display of the selected parameter (satellite product) on a map
            # case2 : the parameter has a depth variable
            lons2 = ds2.variables['lon'][:]
            lats2 = ds2.variables['lat'][:]
            variable_ds2 = ds2.variables[varb2][:]
            lon2, lat2 = np.meshgrid(lons2, lats2)
            map = Basemap(llcrnrlon=7,llcrnrlat=50,urcrnrlon=32,urcrnrlat=70, epsg=4326)
            x2, y2 = map(lon2, lat2)
            np.seterr(divide='ignore', invalid='ignore')
            fig = plt.figure()
            if scale == 'Same_as_Model_Product':
                contourf_ds2 = plt.contourf(x2,y2,variable_ds2[0,0,:,:],cmap=plt.cm.jet,vmin=scale_min, vmax=scale_max);
            else:
                contourf_ds2 = plt.contourf(x2,y2,variable_ds2[0,0,:,:],cmap=plt.cm.jet);
            geojson_ds2 = geojsoncontour.contourf_to_geojson(
                contourf=contourf_ds2,
                min_angle_deg=3.0,
                ndigits=5,
                stroke_width=1,
                fill_opacity=1)
            plt.close(fig)
            #---------------------------------------------------------------------------------------
        
        # get the values of the selected parameter on the surface (depth = 0) for all netcdf files
        var_temp_test2=[]
        for i in range(len(All_ds)):
            if All_ds[i][param][0].size > 1:
                var_temp_test=All_ds[i][param][0,0]
                var_temp_test2.append(var_temp_test)
            else:
                var_temp_test=All_ds[i][param][0]
                var_temp_test2.append(var_temp_test)
        var_temp_test2=np.asarray(var_temp_test2, dtype=np.float)[:]
        #--------------------------------------------------------------------------------------------

        # get the values of the latitude of the selected parameter on the surface (depth = 0) for all netcdf files
        lats_test2=[]
        for i in range(len(All_ds)):
            lats_test=All_ds[i]['LATITUDE'][0]
            lats_test2.append(lats_test)
        lats_test2=np.asarray(lats_test2, dtype=np.float)[:]
        #--------------------------------------------------------------------------------------------------------

        # get the values of the longitude of the selected parameter on the surface (depth = 0) for all netcdf files
        lons_test2=[]
        for i in range(len(All_ds)):
            lons_test=All_ds[i]['LONGITUDE'][0]
            lons_test2.append(lons_test)
        lons_test2=np.asarray(lons_test2, dtype=np.float)[:]

        index_nan=np.where(np.isnan(var_temp_test2))
        var_temp_test3=np.delete(var_temp_test2,index_nan)
        lons_test3=np.delete(lons_test2,index_nan)
        lats_test3=np.delete(lats_test2,index_nan)    
        
        cmap=mpl.cm.jet
        if scale =='Same_as_Model_Product':
            nn=mpl.colors.Normalize(vmin=scale_min, vmax=scale_max)
        else:
            nn=mpl.colors.Normalize(vmin=var_temp_test3.min(), vmax=var_temp_test3.max())
        
        #-------------------------------------------------------------------------------------------    
        
        # Setup colormap
        colors = ['#d7191c',  '#fdae61',  '#ffffbf',  '#abdda4',  '#2b83ba']
        levels = len(colors)
        cm     = branca.colormap.LinearColormap(colors, vmin=scale_min, vmax=scale_max).to_step(levels)

        # create the interactive map (folium)
        geomap = folium.Map(location=[60, 15], zoom_start=4, tiles="cartodbpositron")
        
        ######################## add the different layers to the interactive map
        
        # add the geojson file of the model product as a layer to the folium map
        folium.GeoJson(
            geojson,
            name=f'CMEMS data: {variable_title} (Model_Product)',
            style_function=lambda x: {
                'color':     x['properties']['stroke'],
                'weight':    x['properties']['stroke-width'],
                'fillColor': x['properties']['fill'],
                'opacity':   0.6,
                'fillOpacity': 1,
            }).add_to(geomap)
        #-------------------------------------------
        
        # add the geojson file of the satellite product as a layer to the folium map
        folium.GeoJson(
            geojson_ds2,
            name=f'CMEMS data: {varb2} (Satellite_Product)',
            style_function=lambda x: {
                'color':     x['properties']['stroke'],
                'weight':    x['properties']['stroke-width'],
                'fillColor': x['properties']['fill'],
                'opacity':   0.6,
                'fillOpacity': 1,
            }).add_to(geomap)
        #-------------------------------------------
        
        # add the Insitu product as a layer to the folium map
        fg = folium.FeatureGroup(name=f"CMEMS data: {param} (Insitu_Product)")
        for lt, ln, el in zip(lats_test3, lons_test3, var_temp_test3):
            fg.add_child(folium.CircleMarker(location=(lt, ln), radius = 6, popup=str(el)+" m",
             color=mpl.colors.rgb2hex(cmap(nn(el))[:3]), fill_opacity=1,fill=True))
        geomap.add_child(fg)
        #-----------------------------------------------------
        
        # add the wms of the sentinel 1 (mundi)  as a layer to the folium map
        folium.raster_layers.WmsTileLayer(
            url= wms_Sentinel1, #'http://shservices.mundiwebservices.com/ogc/wms/88b68ca0-1f84-4286-8359-d3f480771de5',
            layers=Sentinel1_layer, #'IW_VV_DB',
            name='Base layer: Sentinel 1 (Mundi) ',
            fmt='image/png',
            overlay=False,
            control=True,
        ).add_to(geomap)
        #-------------------------------------------
        
        # add the wms of the sentinel 2 (mundi)  as a layer to the folium map
        folium.raster_layers.WmsTileLayer(
           url=wms_Sentinel2,   #'http://shservices.mundiwebservices.com/ogc/wms/d275ef59-3f26-4466-9a60-ff837e572144',
           layers=Sentinel2_layer, #'1_NATURAL_COL0R',
           name='Base layer: Sentinel 2 (Mundi)',
           fmt='image/png',
           overlay=False,
           control=True,
           previewMode= "EXTENDED_PREVIEW",
        ).add_to(geomap)
        #-------------------------------------------
        
        # add the wms of the sentinel 2 (sentinelhub)  as a layer to the folium map
        folium.raster_layers.WmsTileLayer(
            url='http://services.sentinel-hub.com/ogc/wms/a1835742-1d93-4114-b0bd-89c2ef747240',
            layers='TRUE-COLOR-S2-L2A',
            name='Base layer: Sentinel 2 (Sentinel Hub)',
            fmt='image/png',
            overlay=False,
            control=True,
            maxcc=5,
            previewMode= "EXTENDED_PREVIEW",
        ).add_to(geomap)
        #-------------------------------------------

        # add the wms of the sentinel 2 cloudless mosaic 2018 (eox)  as a layer to the folium map
        folium.raster_layers.WmsTileLayer(
            url='https://tiles.maps.eox.at/wms?service=wms',
            layers='s2cloudless-2018_3857',
            name='Base layer: Sentinel2 Cloudless mosaic 2018',
            fmt='image/png',
            overlay=False,
            control=True,
            version='1.1.1',
        ).add_to(geomap)
        #-------------------------------------------

        # add google maps as a layer to the folium map
        folium.raster_layers.TileLayer(
            tiles='http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr='google',
            name='Base layer: google maps',
            max_zoom=20,
            subdomains=['mt0', 'mt1', 'mt2', 'mt3'],
            overlay=False,
            control=True,
        ).add_to(geomap)
        #-------------------------------------------

        # add  google street view as a layer to the folium map
        folium.raster_layers.TileLayer(
            tiles='http://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
            attr='google',
            name='Base layer: google street view',
            max_zoom=20,
            subdomains=['mt0', 'mt1', 'mt2', 'mt3'],
            overlay=False,
            control=True,
        ).add_to(geomap)
        #-------------------------------------------
        
        # add fullscreen option to the map
        plugins.Fullscreen(position='topright', force_separate_button=True).add_to(geomap)
        folium.LayerControl().add_to(geomap)
        #-------------------------------------------
        
        # save the map as folium_map.html
        geomap.save(output_directory+'/folium_map.html')  
        print('Done')

        return geomap
        #-------------------------------------------
