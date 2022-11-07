#%%

from operator import index
import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def analyze_sed_del(wshed,SDR,TMDL_SD,TMDL_RO,mod_lst,ymin,ymax,per_adopt_lst,wshed_name):
    '''
    Analyze sediment delivery and runoff outputs for all watersheds, management scenarios, and climate 
    models. Data is loaded and prepped in with prep_SL_RO_data function. The
    prepped data is then visualized with the graph_soil_del function.

    wshed_lst = list of watershed names 
    scen_lst = list of future management scenario IDs
    mod_lst = list of future climate model IDs
    '''


    def prep_SL_RO_data(wepp_out_dir,years):
        '''
        Loads in wepp output data from .ebe and .loss files. Extracts soil loss
        values from .ebe, averages them by hillslope over entire period,
        and then converts the average to a mass/area sediment delivery value using
        profile width and area values extracted from the .loss files and the calculated
        sediment delivery ratio (SDR).

        wepp_out_dir = WEPP watershed/scenario/clim model output directory 

        years = total number of years in climate period

        output_lst = output list that will hold average sediment delivery value for each hillslope
        '''


        ##### Load in .ebe and .loss files ######

        #get ebe files from output directory
        hillslopes = [x for x in os.listdir(wepp_out_dir) if x.endswith('.ebe.dat')]

        #define column names for ebe file load in
        ebe_col_list = ['Day', 'Month', 'Year', 'Precip', 'RO', 'IR-det',\
                        'Av-det', 'Mx-det', 'Point', 'Av-dep', 'Mx-dep',\
                        'Point_2', 'Sed-Del', 'ER']



        #get loss files from output directory
        loss_files = [x for x in os.listdir(wepp_out_dir) if x.endswith('.loss.dat')]


        #output list that will hold average sediment delivery values for each hillslope
        SD_lst = []
        TMDL_SD_lst = []
        RO_lst = []
        TMDL_RO_lst = []

        ##### Prep data for graphing ######

        #loop through all .loss and .ebe files
        for file, hill in zip(loss_files,hillslopes):

            #open .loss for reading
            with open(str(wepp_out_dir + file), 'r') as loss_data:

                #loop through lines
                for line in loss_data:

                    #select line if it contains this key phrase:
                    if 'kg (based on profile width of' in line:

                        #extract numbers from line
                        nums = []
                        for n in line.split():
                            try:
                                nums.append(float(n))
                            except ValueError:
                                pass
                        
                        #get hillslope profile width in meters
                        width = nums[1]

                    #select line if it contains this key phrase:
                    if 't/ha (assuming contributions from' in line:

                        #extract numbers from line
                        nums = []
                        for n in line.split():
                            try:
                                nums.append(float(n))
                            except ValueError:
                                pass
                        
                        #get hillslope area in hectares
                        area = nums[1]
                        
            
            #read in ebe file to dataframe
            all_data = pd.read_csv(str(wepp_out_dir+hill), skiprows = 3,\
                                    names = ebe_col_list, sep = '\s+', header=None)

            season_data = all_data[all_data['Month'] > 3]
            season_data = season_data[season_data['Month'] < 12]


            #get average sediment delivery for entire period
            #divide sum by total number of years,
            #multiple by sed delivery value (in kg/m) by profile width to get kg,
            #convert from kg to tons,
            #divide by area to get avg sediment delivery in tons/ha

            if area > 0:
                #calculate average sediment delivery during the growing season or spring/fall/summer
                avg_SD= ((((season_data['Sed-Del'].sum() / years) * width) * 0.00110231) / area) * SDR
                #append to hillslope
                SD_lst.append(avg_SD)


                if avg_SD > TMDL_SD:
                    TMDL_SD_lst.append(avg_SD)


            if area == 0:
                pass
            
            #calculate average runoff during the growing season or spring/fall/summer
            avg_RO = season_data['RO'].sum() / years
            RO_lst.append(avg_RO)

            if avg_RO > TMDL_RO:
                TMDL_RO_lst.append(avg_RO)


        #Get average total sediment delivery for entire watershed
        total_SD= sum(SD_lst) / len(hillslopes)

        #Get the percentage of hillslopes in a watershed above TMDL field sediment delivery
        total_TMDL_SD = (len(TMDL_SD_lst) / len(hillslopes)) * 100

        #Get average total runoff for entire watershed
        total_RO = sum(RO_lst) / len(hillslopes)

        #Get the percentage of hillslopes in a watershed abvove TMDL runoff
        total_TMDL_RO = (len(TMDL_RO_lst) / len(hillslopes)) * 100

        return total_SD, total_TMDL_SD, total_RO, total_TMDL_RO


    #set up groups of scenarios. Each group will be plotted into an ecdf
    #for each climate model. Climate models will be combined onto each
    #management scenario plot

    scen_types = [['Per_0', 'CC_10', 'CC_20'],\
                  ['Per_0', 'CT_50', 'CT_100'],\
                  ['Per_0','Per_m20','Per_B','Per_p20'],\
                  ['Per_0_100','Per_m20_100','Per_B_100','Per_p20_100']]

    # define % Adoption rates for each management scenario 
    adopt_rates = [[1, 10, 20],\
                   [30, 50, 100],\
                   per_adopt_lst,\
                   per_adopt_lst]

    # define management scenario names
    scen_names = ['Cover Cropping',\
                  'Conservation Tillage',\
                  'Perennial Integration',\
                  'Perennial Integration with 100% Consv. Till.']


    #Set up a subplot for each watershed that contains plots for each watershed
    fig, axes = plt.subplots(nrows = 2, ncols = 2, figsize = (22,22))

    #subplot x and y coordinate values. Used to position subplots.
    subx_vals = [0,0,1,1]
    suby_vals = [0,1,0,1]

    def graph_prepped_data(graphed_var, TMDL_val, out_lab, y_lab):

        '''
        Run prep_SL_RO_data function for all climate scenarios for
        sediment delivery or runoff (determined via graphed_var input)

        Then set up dataframe with all values for each climate mod, plot data points,
        and repeat for all management scenarios.

        graphed_var = string input that defines which output variable is used from 
        the prep_sed_del_data function

        y_lab = y axis label
        '''

        #loop through each scenario and adoption % in scenario type list
        for scen_lst, adopt_lst, subx, suby, scen_name in zip(scen_types,adopt_rates,subx_vals,suby_vals, scen_names):


            #set up output lists for each climate model
            B3_59 = []
            B3_99 = []
            B4_59 = []
            B4_99 = []
            L3_59 = []
            L3_99 = []
            L4_59 = []
            L4_99 = []
            Obs = []

            #create list of lists
            mod_out_lsts = [B3_59, B3_99, B4_59, B4_99,\
                            L3_59, L3_99, L4_59, L4_99,\
                            Obs]

            #create dictionary to hold unsustainable sediment delivery vals from each scen/clim mod
            table_dic = {}

            #Run function for all climate models and scenarios
            for mod, mod_out_lst in zip(mod_lst, mod_out_lsts):

                table_lst = []

                for scen in scen_lst:
                    
                    #define number of years in model period
                    if mod == 'Obs':
                        years = 55

                    if mod != 'Obs':
                        years = 40
                    
                    #define wepp output directory where data is stored
                    wepp_out_dir = str('C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/New_Runs/{}/{}/wepp/output/'.format(wshed,mod,scen))

                    #run prep_SL_RO_data using defined number of years and wepp output directory
                    sed_del, TMDL_SD, runoff, TMDL_RO = prep_SL_RO_data(wepp_out_dir, years)
                    
                    #append output value to list depending on function input
                    if graphed_var == 'sed_del':
                        mod_out_lst.append(sed_del)
                        table_lst.append(sed_del)

                    if graphed_var == 'runoff':
                        mod_out_lst.append(runoff)
                        table_lst.append(runoff)

                    if graphed_var == 'TMDL_SD':
                        mod_out_lst.append(TMDL_SD)
                        table_lst.append(TMDL_SD)

                    if graphed_var == 'TMDL_RO': 
                        mod_out_lst.append(TMDL_RO)
                        table_lst.append(TMDL_RO)

                table_dic[f'{mod}_{scen}'] = table_lst

            table_df = pd.DataFrame.from_dict(table_dic,orient='index').transpose()

            table_df.to_excel('C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/Future_Man_Outputs/{}/{}_{}.xlsx'.format(out_lab, wshed,scen_name))

            #Set up dataframe with model names as column heads
            output_df = pd.DataFrame({'GFDL-ESM2G 4.5 2020-59':B3_59,\
                                        'GFDL-ESM2G 4.5 2060-99':B3_99,\
                                        'GFDL-ESM2G 6.0 2020-59':B4_59,\
                                        'GFDL-ESM2G 6.0 2060-99':B4_99,\
                                        'HadGEM2-CC 4.5 2020-59':L3_59,\
                                        'HadGEM2-CC 4.5 2060-99':L3_99,\
                                        'HadGEM2-CC 8.5 2020-59':L4_59,\
                                        'HadGEM2-CC 8.5 2060-99':L4_99,\
                                        'Baseline 1965-2019':Obs,
                                        '% Adoption':adopt_lst},\
                                        index = scen_lst)  


            mod_names = ['GFDL-ESM2G 4.5 2020-59','GFDL-ESM2G 4.5 2060-99',\
                         'GFDL-ESM2G 6.0 2020-59','GFDL-ESM2G 6.0 2060-99',\
                         'HadGEM2-CC 4.5 2020-59','HadGEM2-CC 4.5 2060-99',\
                         'HadGEM2-CC 8.5 2020-59','HadGEM2-CC 8.5 2060-99',\
                         'Baseline 1965-2019']

            point_shapes = ['-o','-v','-^','-s','-P','-D','-<','->','-x']

            colors = ['deepskyblue', 'mediumblue',\
                    'red', 'darkred',\
                    'limegreen', 'darkgreen',\
                    'fuchsia', 'purple',\
                    'black']

            def create_plot(df,mod, point_shape, color):

                x = df['% Adoption']
                y = df[mod]

                #plot data
                axes[subx,suby].plot(x,y, point_shape, label = mod, color = color)

                #standardize y-axis
                axes[subx,suby].set_ylim(bottom = ymin, top = ymax) 

                #set axis labels
                axes[subx,suby].set_xlabel('Adoption across Watershed (%)', fontsize = 22)
                axes[subx,suby].set_ylabel(y_lab, fontsize = 22)

                axes[subx,suby].tick_params(labelsize = 18)

                #set subplot titles
                axes[subx,suby].set_title(scen_name, fontsize = 22)

                axes[subx,suby].grid()

                #set vertical line for TMDL

                axes[subx,suby].axhline(y=TMDL_val, color='gold')


            #loop through model names and colors, then plot
            for mod_name, point_shape, color in zip(mod_names,point_shapes, colors):
                create_plot(output_df,mod_name,point_shape,color)

    graph_prepped_data('runoff', TMDL_RO, 'Runoff', 'Average Total Hillslope Runoff (mm)')

    #create legend
    handles, labels = axes[0,1].get_legend_handles_labels()

    handles.append((plt.Line2D([], [], color='gold')))

    labels.append('-50% Watershed TSS TMDL')

    fig.legend(handles, labels, bbox_to_anchor = [1.15,0.85],fontsize=20)

    fig.suptitle('Average Total Growing Season Hillslope Runoff in {} County, MN HUC12 Watershed\nwith Varying Management Scenarios and Future Climates'.format(wshed_name),\
                 fontsize = 24)

    fig.subplots_adjust(top=0.92)

    fig.savefig('C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/Future_Man_Outputs/Runoff/{}_.png'.format(wshed), bbox_inches = "tight")


#Example for runoff figures

mod_lst = ['B3_59', 'B3_99', 'B4_59', 'B4_99',\
           'L3_59', 'L3_99', 'L4_59', 'L4_99',\
           'Obs']    

S_ymin = 0 #ST1
S_ymax = 40 #ST1
ST1_per_adopt = [0, 30, 50, 66]

G_ymin = 0 #GO1
G_ymax = 40 #GO1
GO1_per_adopt = [0, 42, 62, 79.1]

D_ymin = 0 #GO1
D_ymax = 40 #GO1
DO1_per_adopt = [0, 25, 45, 72]

#Run function for each watershed
analyze_sed_del('DO1', 0.0645, 0.129, 15.8, mod_lst, D_ymin, D_ymax, DO1_per_adopt, 'Dodge')
analyze_sed_del('GO1', 0.0643, 0.131, 10.7, mod_lst, G_ymin, G_ymax, GO1_per_adopt, 'Goodhue')
analyze_sed_del('ST1', 0.0296, 0.013, 13.8, mod_lst, S_ymin, S_ymax, ST1_per_adopt, 'Stearns')
