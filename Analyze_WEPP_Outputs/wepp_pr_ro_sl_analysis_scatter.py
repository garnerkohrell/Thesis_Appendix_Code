#%%
import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import ScalarFormatter
from matplotlib.axis import Axis 
from prep_for_analysis_scatter import prep_data


def analyze_wepp_outputs(wshed,wshed_name,mod_pair,mod_name,period_names):
    '''
    Analyze wepp soil loss and runoff trends as well as
    cligen precipitation trends using scatterplots with 
    event-by-event data

    wshed = watershed ID

    mod_pair = list of future and observed climate model IDs

    mod_name = name of CMIP5 climate model

    period_names = time periods (ex: 1965-2019)
    '''


    ####### GET SEASONAL FIGURES #########

    #use to loop through months used for selecting the months corresponding to each season
    season_start_months = [4,6,9,4]
    season_end_months = [5,8,11,11]
    season_names = ['Spring','Summer', 'Fall', 'Growing Season']

    #Set up a subplot to hold seasonal data
    fig_s, ax_s = plt.subplots(nrows = 3, ncols = 2, figsize = (27,32))

    #Set up a subplot to hold growing season data
    fig_gs, ax_gs = plt.subplots(nrows = 1, ncols = 2, figsize = (27,12))


    suby_vals = [0,1]

    color_lst = ['skyblue', 'dodgerblue', 'darkblue']

    for season_start,season_end,season_name in zip(season_start_months, season_end_months, season_names):

        #chose subplot x coordinate if loop is in a season, do not chose one if in growing season
        if season_name == 'Spring':
            subx = 0

        if season_name == 'Summer':
            subx = 1

        if season_name == 'Fall':
            subx = 2

        #define subplot dimensions and axes names 
        if season_name == 'Growing Season':
            dimensions = '1D'
            axes = ax_gs

        else:
            dimensions = '2D'
            axes = ax_s


        for mod,period,color in zip(mod_pair,period_names,color_lst):

            #define wepp output directory where data is stored
            wepp_out_dir = str('C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/New_Runs/{}/Per_B/wepp/output/'.format(wshed,mod))
            wepp_cli_dir = str('C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/New_Runs/{}/Per_B/wepp/runs/'.format(wshed,mod))

            #run prep_data
            SL, RO, PR, PRi = prep_data(wepp_cli_dir,wepp_out_dir,mod,season_start,season_end)


            #set up values and labels for plotting
            var_ylabs = ['Soil Loss Events (tons/ha)',\
                        'Runoff Events (mm)']

            yvars = [SL,RO]

            for suby,yvar,var_ylab in zip(suby_vals,yvars,var_ylabs):

                x = PR
                y = yvar

                if dimensions == '2D':
                    subplt = axes[subx,suby]
                
                if dimensions == '1D':
                    subplt = axes[suby]

                subplt.scatter(x,y,color = color, s=11, label = period, alpha = 0.7)

                #set axis labels
                subplt.set_ylabel(var_ylab, fontsize = 20)

                #set axis labels
                subplt.set_xlabel('Precipitation Depth (mm)', fontsize = 20)
                
                #increase size of tick labels
                subplt.tick_params(labelsize = 16)

                subplt.set_title(season_name)

                subplt.grid()


    #create legends and titles for plots
    handles, labels = ax_s[1,1].get_legend_handles_labels()

    fig_s.legend(handles, labels, bbox_to_anchor = [1.0,0.85],fontsize=16)

    fig_s.suptitle('WEPP Hillslope Events vs Precipitation Depths by Season\n {} County HUC12 Watershed with Baseline and Future Climates ({})'.format(wshed_name,mod_name),\
                fontsize = 25)

    fig_s.subplots_adjust(top=0.92)


    fig_gs.legend(handles, labels, bbox_to_anchor = [1.0,0.85],fontsize=16)

    fig_gs.suptitle('WEPP Hillslope Events vs Precipitation Depths during Growing Season\n {} County HUC12 Watershed with Baseline and Future Climates ({})'.format(wshed_name,mod_name),\
                fontsize = 25)

    fig_s.savefig('C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/Future_NoChange/{} {} seasons.png'.format(wshed,mod_name))
    fig_gs.savefig('C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/Future_NoChange/{} {} GS.png'.format(wshed,mod_name))



lst_of_mods = [['Obs','B3_59','B3_99'],\
                ['Obs','B4_59','B4_99'],\
                ['Obs','L3_59','L3_99'],\
                ['Obs','L4_59','L4_99']]

mod_names = ['gfdl RCP 4.5', 'gfdl RCP 6.0',\
             'Hadgem2 RCP 4.5', 'Hadgem2 RCP 8.5']

period_names = ['1965-2019', '2020-2059','2060-2099'] 

#Example for Goodhue watershed 

for mod_set, mod_name in zip(lst_of_mods, mod_names):
    analyze_wepp_outputs('GO1', 'Goodhue', mod_set, mod_name, period_names)

#%%