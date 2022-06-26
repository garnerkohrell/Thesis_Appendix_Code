import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import ScalarFormatter
from matplotlib.axis import Axis 
from prep_for_analysis import prep_data


def analyze_wepp_outputs(wshed,wshed_name,mod_sets,mod_names,month_start, month_end, freq_total_input,x_limits):
    '''
    Analyze wepp soil loss and runoff trends as well as
    cligen precipitation trends using ECDFs 

    wshed = watershed ID

    wshed_name = name of watershed

    mod_sets = list of future and observed climate model IDs

    mod_names = names of CMIP5 climate models

    freq_total_input = string input to define whether frequency or total sum
    ECDFs should be created

    x_limits = x-axis limit for variable/watershed combination

    month_start = integer value of month at beginning of season selection

    month_start = integer value of month at end of season selection
    '''


    #Set up a subplot to hold seasonal data
    fig= plt.figure(figsize = (34,28))
    spec = fig.add_gridspec(2,4)

    had_sl = fig.add_subplot(spec[0, 0])
    had_ro = fig.add_subplot(spec[0, 1])
    had_pr = fig.add_subplot(spec[0, 2])
    had_pri = fig.add_subplot(spec[0, 3])
    gf_sl = fig.add_subplot(spec[1, 0])
    gf_ro = fig.add_subplot(spec[1, 1])
    gf_pr = fig.add_subplot(spec[1, 2])
    gf_pri = fig.add_subplot(spec[1, 3])


    #create list for plot colors
    colors = [['black', 'limegreen', 'darkgreen','fuchsia', 'purple'],\
              ['black','deepskyblue', 'mediumblue','red', 'darkred']]

    #create list for legend items
    labels = [['Baseline w/ Perennials 1965-2019','HadGEM2-CC 4.5 2020-59','HadGEM2-CC 4.5 2060-99',\
               'HadGEM2-CC 8.5 2020-59','HadGEM2-CC 8.5 2060-99'],\
              ['_nolegend_','GFDL-ESM2G 4.5 2020-59','GFDL-ESM2G 4.5 2060-99',\
               'GFDL-ESM2G 6.0 2020-59','GFDL-ESM2G 6.0 2060-99']]

    subx_pairs = [[had_sl,had_ro,had_pr,had_pri],[gf_sl,gf_ro,gf_pr,gf_pri]]


    for mod_set, color_set, mod_name, subx_pair,lab_set in zip(mod_sets,colors,mod_names,subx_pairs,labels):

        for mod,color,line_lab in zip(mod_set,color_set,lab_set):

            if mod == 'Obs':
                #define wepp output directory where data is stored
                wepp_out_dir = str('C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/New_Runs/{}/Per_B/wepp/output/'.format(wshed,mod))
                wepp_cli_dir = str('C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/New_Runs/{}/Per_B/wepp/runs/'.format(wshed,mod))

            else:
                #define wepp output directory where data is stored
                wepp_out_dir = str('C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/New_Runs/{}/Per_B/wepp/output/'.format(wshed,mod))
                wepp_cli_dir = str('C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/New_Runs/{}/Per_B/wepp/runs/'.format(wshed,mod))

            #run prep_data for months provided in function input
            SL_lst, RO_lst, PR_lst, PRi_lst, PR, PRi, RO,SL, avg_pr, avg_pri, pr_25, avg_dur,avg_tmax,avg_tmin = prep_data(wepp_cli_dir,wepp_out_dir,mod,month_start,month_end)

            #set up values and labels for plotting ecdfs
            var_lsts = [SL_lst, RO_lst, PR_lst, PRi_lst]
            var_xlabs = ['Avg Total Soil Loss from Field (tons/ha)',\
                         'Avg Total Runoff from Field (mm)',\
                         'Precipitation Depths by Event (mm)',\
                         'Storm Intensities by Event (mm/hr)']


            for subx,var_lst,xlab,xlimit in zip(subx_pair,var_lsts,var_xlabs,x_limits):

                data = pd.Series(var_lst)

                data = data.astype(float)

                x = np.sort(data)

                #if input for freq_total_input == freq, plot ecdf for event frequency
                if freq_total_input == 'Frequency':
                    n = x.size
                    y = (np.arange(1, n+1) / n) * 100
                    ylab = 'ECDF = Cumulative Frequency (%)'

                #if input for freq_total_input == freq, plot ecdf for total (loss)/(mm)/(mm/hr)
                if freq_total_input == 'Total Sum':
                    y = (np.cumsum(x) / sum(x)) * 100
                    ylab = 'ECDF = Cumulative Total (%)'

                subx.scatter(x,y, s=35, color = color, label = line_lab)

                #set axis labels
                subx.set_xlabel(xlab, fontsize = 25)

                subx.set_ylabel(ylab, fontsize = 25)

                if var_lst == SL_lst:
                    subx.axvline(x=12.5, color='dimgrey')
                
                #increase size of tick labels
                subx.tick_params(labelsize = 20)

                subx.set_title(mod_name, fontsize = 27)

                subx.set_xlim(0,xlimit)

                subx.grid()
    
    fig.suptitle('{} ECDFs for Average Total Soil Loss and Runoff during Minnesota Spring by Hillslope 1965-2099:\n{} County HUC12 Watershed'.format(freq_total_input,wshed_name),\
                fontsize = 30)

    fig.subplots_adjust(top=0.92)

    #create legend
    handles1, labels1 = had_sl.get_legend_handles_labels()
    handles2, labels2 = gf_sl.get_legend_handles_labels()
    fig.legend(handles1, labels1, bbox_to_anchor = [1.12,0.90],fontsize=25,markerscale=3,frameon=False)
    fig.legend(handles2, labels2, bbox_to_anchor = [1.08,0.81],fontsize=25,markerscale=3,frameon=False)
    


    fig.savefig('C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/Future_NoChange/ECDFs/{}_{}_ECDF.png'.format(wshed,freq_total_input), bbox_inches = "tight")

#define watershed list
wshed_lst = ['DO1', 'GO1', 'ST1']

#define watershed names
wshed_names = ['Dodge', 'Goodhue', 'Stearns']

#define climate model IDs
mod_sets = [['Obs','L3_59','L3_99','L4_59','L4_99'],\
            ['Obs','B3_59','B3_99','B4_59','B4_99']]

#define climate model names
mod_names = ['HadGEM2-CC',\
             'GFDL-ESM2G']

#set x-axis limit for each watershed and variable
DO1_limits = [4,20,150,60]
GO1_limits = [6,20,200,100]
ST1_limits = [3,20,100,80]

#get list of lists for x-axis limits
wshed_xlimits = [DO1_limits, GO1_limits, ST1_limits]


#Example run using frequency ECDFs and baseline management for the entire growing season
#month_start and month_end can be switched to run for different seasons.



for wshed, wshed_name, wshed_xlim in zip(wshed_lst, wshed_names, wshed_xlimits):
    analyze_wepp_outputs(wshed, wshed_name, mod_sets, mod_names, 4, 11, 'Frequency', wshed_xlim)