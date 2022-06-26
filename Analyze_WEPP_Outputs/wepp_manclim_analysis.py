#%%

from operator import index
import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def analyze_soil_loss(wshed,mod_lst,ymin,ymax,per_adopt_lst,wshed_name):
    '''
    Analyze soil loss and runoff outputs for all watersheds, management scenarios, and climate 
    models. Data is loaded and prepped in with prep_SL_RO_data function. The
    prepped data is then visualized with the graph_soil_losses function.

    wshed_lst = list of watershed names 
    scen_lst = list of future management scenario IDs
    mod_lst = list of future climate model IDs
    '''


    def prep_SL_RO_data(wepp_out_dir,years):
        '''
        Loads in wepp output data from .ebe and .loss files. Extracts Sediment
        delivery values from .ebe, averages them by hillslope over entire period,
        and then converts the average to a mass/area soil loss value using
        profile width and area values extracted from the .loss files.

        wepp_out_dir = WEPP watershed/scenario/clim model output directory 

        years = total number of years in climate period

        output_lst = output list that will hold average soil loss value for each hillslope
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


        #output list that will hold average soil loss values for each hillslope
        loss_lst = []
        unsustain_lst = []
        RO_lst = []

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


            #get average loss for entire period
            #divide sum by total number of years,
            #multiple by sed delivery value (in kg/m) by profile width to get kg,
            #convert from kg to tons,
            #divide by area to get avg soil loss in tons/ha

            if area > 0:
                #calculate average soil loss during the growing season or spring/fall/summer
                avg_loss = (((season_data['Sed-Del'].sum() / years) * width) * 0.00110231) / area
                #append to hillslope
                loss_lst.append(avg_loss)


                if avg_loss > 12.5:
                    unsustain_lst.append(avg_loss)


            if area == 0:
                pass
            
            #calculate average runoff during the growing season or spring/fall/summer
            avg_runoff_depth = season_data['RO'].sum() / years
            RO_lst.append(avg_runoff_depth)


        #Get average total soil loss for entire watershed
        total_loss = sum(loss_lst) / len(hillslopes)

        #Get the percentage of hillslopes in a watershed with unsustainable soil loss
        total_unsustain_loss = (len(unsustain_lst) / len(hillslopes)) * 100

        #Get average total runoff for entire watershed
        total_RO = sum(RO_lst) / len(hillslopes)

        return total_loss, total_unsustain_loss, total_RO


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

    def graph_prepped_data(graphed_var, y_lab):

        '''
        Run prep_SL_RO_data function for all climate scenarios for
        soil loss or runoff (determined via graphed_var input)

        Then set up dataframe with all values for each climate mod, plot data points,
        and repeat for all management scenarios.

        graphed_var = string input that defines which output variable is used from 
        the prep_soil_loss_data function

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

            #create dictionary to hold unsustainable loss percentages from each scen/clim mod
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
                    soil_loss, unsustain_loss, runoff = prep_SL_RO_data(wepp_out_dir, years)
                    
                    #append output value to list depending on function input
                    if graphed_var == 'soil_loss':
                        mod_out_lst.append(soil_loss)
                        table_lst.append(soil_loss)

                    if graphed_var == 'runoff':
                        mod_out_lst.append(runoff)
                        table_lst.append(runoff)

                    if graphed_var == 'unsustain': #unsustain = unsustainble soil loss
                        mod_out_lst.append(unsustain_loss)
                        table_lst.append(unsustain_loss)

                table_dic[f'{mod}_{scen}'] = table_lst

            table_df = pd.DataFrame.from_dict(table_dic,orient='index').transpose()

            table_df.to_excel('C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/Future_Man_Outputs/Soil_Loss/{}_{}.xlsx'.format(wshed,scen_name))

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

            colors = ['deepskyblue', 'mediumblue',\
                    'red', 'darkred',\
                    'limegreen', 'darkgreen',\
                    'fuchsia', 'purple',\
                    'black']

            def create_plot(df,mod,color):

                x = df['% Adoption']
                y = df[mod]

                #plot data
                axes[subx,suby].plot(x,y, '-o',label = mod, color = color)

                #standardize y-axis
                axes[subx,suby].set_ylim(bottom = ymin, top = ymax)

                #set axis labels
                axes[subx,suby].set_xlabel('Adoption across Watershed (%)', fontsize = 22)
                axes[subx,suby].set_ylabel(y_lab, fontsize = 22)

                axes[subx,suby].tick_params(labelsize = 18)

                #set subplot titles
                axes[subx,suby].set_title(scen_name, fontsize = 22)

                axes[subx,suby].grid()


            #loop through model names and colors, then plot
            for mod_name, color in zip(mod_names,colors):
                create_plot(output_df,mod_name,color)

    graph_prepped_data('soil_loss', 'Average Total Hillslope Soil Loss (t/ha)')

    #create legend
    handles, labels = axes[0,1].get_legend_handles_labels()
    fig.legend(handles, labels, bbox_to_anchor = [1.15,0.85],fontsize=20)

    fig.suptitle('Average Total Growing Season Hillslope Soil Loss in {} County, MN HUC12 Watershed\nwith Varying Management Scenarios and Future Climates'.format(wshed_name),\
                 fontsize = 24)

    fig.subplots_adjust(top=0.92)

    fig.savefig('C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/Future_Man_Outputs/Soil_Loss/{}_.png'.format(wshed), bbox_inches = "tight")




mod_lst = ['B3_59', 'B3_99', 'B4_59', 'B4_99',\
           'L3_59', 'L3_99', 'L4_59', 'L4_99',\
           'Obs']    

S_ymin = 0 #ST1
S_ymax = 3 #ST1
ST1_per_adopt = [0, 30, 50, 66]

G_ymin = 0 #GO1
G_ymax = 9 #GO1
GO1_per_adopt = [0, 42, 62, 79.1]

D_ymin = 0 #GO1
D_ymax = 8 #GO1
DO1_per_adopt = [0, 25, 45, 72]

#Run function for each watershed
analyze_soil_loss('DO1', mod_lst, D_ymin, D_ymax, DO1_per_adopt, 'Dodge')
analyze_soil_loss('GO1', mod_lst, G_ymin, G_ymax, GO1_per_adopt, 'Goodhue')
analyze_soil_loss('ST1', mod_lst, S_ymin, S_ymax, ST1_per_adopt, 'Stearns')
