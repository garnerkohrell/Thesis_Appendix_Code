import pandas as pd
import hydroeval as he

def NSE_PBIAS_Analysis(obs_dir, wshed, cli_dir, wepp_out_dir, hillID, mod_yrs, TSS_adjust, crop1_yrs, crop2_yrs, obs_rot):
    '''
    Loads in Precip, RO, and TSS data and preps for NSE and PBIAS analyses

    Performs NSE and PBIAS analyses using mean monthly runoff ratio

    obs_dir = directory containing observed data
    wshed = watershed/site name
    cli_dir = directory containing cligen file (same as wepp run dir)
    wepp_out_dir = directory containing wepp output files
    hillID = ID of WEPP hillslope in simulated site run
    mod_rot_starters = integers corresponding to years in the observed crop rotation
    obs_rot = years (not short integers)  in observed crop rotation
    '''

    import pandas as pd
    import numpy as np
    import os
    import hydroeval as he

    ###### load in climate data and fill in missing obs values ######

    #Create path to daily DF data and read into df
    DF_daily_xlsx = str(obs_dir + '{}_daily_DF.xlsx'.format(wshed))
    DF_df = pd.read_excel(DF_daily_xlsx)
    DF_df['DF_pr'] = (DF_df['Pr'].apply(pd.to_numeric, errors='coerce')) * 25.4

    #Read in and prep cligen data
    cli_df = pd.read_csv(str(cli_dir + '/{}.cli'.format(hillID)), skiprows = 13, sep = '\s+| ', engine = 'python')
    cli_df.drop([0,], axis = 0, inplace = True)
    cli_df.reset_index(inplace = True)
    cli_df['Month'] = cli_df['mo'].astype(int)
    cli_df['cli_pr'] = cli_df['prcp'].astype(float)
    cli_sub = cli_df[cli_df['year'].astype(int).isin(mod_yrs)].reset_index()

    #concatenate cligen precip column to DF df and return new df
    comb_df = pd.concat([DF_df, cli_sub['cli_pr']], axis=1)

    #If DF col is missing data, fill in with cligen data using np.where()
    comb_df['filled_pr'] = (np.where(comb_df['DF_pr'].isna(),\
                                    comb_df['cli_pr'],\
                                    comb_df['DF_pr']))
    
    #select march-november for precip
    comb_df_sel = comb_df[comb_df['Month'].astype(int) > 3]
    comb_df_sel = comb_df_sel[comb_df_sel['Month'].astype(int) < 12]

    cli_df_sel = cli_df[cli_df['Month'].astype(int) > 3]
    cli_df_sel = cli_df_sel[cli_df_sel['Month'].astype(int) < 12]



    ###### prep runoff/TSS data ######


    ###### Load in runoff and soil loss data ######

    #Load in observed data (whole dataset)
    obs_data_whole = pd.read_excel(str(obs_dir + '/{}_Obs_RO.xlsx'.format(wshed)))

    #select data for March-November
    obs_data_months = obs_data_whole[obs_data_whole['Month'].astype(int) > 3]
    obs_data_months = obs_data_months[obs_data_months['Month'].astype(int) < 12]

    #trim down data column to only include day, month, and year
    obs_data_months['Start'] = obs_data_months['Start'].astype(str).str[0:10]
    obs_data_months['End'] = obs_data_months['End'].astype(str).str[0:10]

    #observed data occasionally has multiple events on same day. Combine these into daily values
    aggregation_functions = {'Start': 'first', 'End':'first', 'Year': 'first', 'Month': 'first',\
                            'Day':'first', 'RO (in)':'sum', 'TSS (lbs/ac)':'sum'}

    obs_data_months = obs_data_months.groupby([obs_data_months['Start'],obs_data_months['End']]).aggregate(aggregation_functions)

    #convert runoff from in to mm  and TSS from lbs/ac to tons/ha in observed data
    #Adjust TSS data so that only suspended sediments are accounted for
    obs_data_months['RO'] = obs_data_months['RO (in)'] * 25.4
    obs_data_months['TSS'] = (obs_data_months['TSS (lbs/ac)'] * 0.00123553) * float(TSS_adjust) #tons/ha

    #Read in data from ebe WEPP output file for a specified calibration scenario

    #get ebe file from output directory
    hillslopes = [x for x in os.listdir(wepp_out_dir) if x.endswith('.ebe.dat')]

    #only one hillslope in DF simulations so just select first file in list
    hill = hillslopes[0]

    #define column names for ebe file load in
    ebe_col_list = ['Day', 'Month', 'Year', 'Precip', 'RO', 'IR-det',\
                    'Av-det', 'Mx-det', 'Point', 'Av-dep', 'Mx-dep',\
                    'Point_2', 'Sed-Del', 'ER']

    #read in ebe file to dataframe
    all_data = pd.read_csv(str(wepp_out_dir+hill), skiprows = 3,\
                        names = ebe_col_list, sep = '\s+', header=None)

    all_data['TSS'] = all_data['Av-det'] * 11.0231

    #select data for March-November
    sel_mod_data = all_data[all_data['Month'] > 3] 
    mod_data_months = sel_mod_data[sel_mod_data['Month'] < 12]



    ## Obs data ##


    ## merge observed precip to observed runoff/TSS events for removing snow melt runoff events

    event_precip = []

    #sum daily precip values by the corresponding runoff events
    for start,end in zip(obs_data_months['Start'], obs_data_months ['End']):

        #if daily precip vals are within date range, select and sum
        matched_pr = comb_df[(comb_df['Date'] >= start) & (comb_df['Date'] <= end)]
        event_pr = matched_pr['filled_pr'].sum()
        event_precip.append(event_pr)
        
    #set summed precip values as Pr column. Each row corresponds to a runoff event
    obs_data_months['Pr'] = event_precip

    #loop through runoff events (df rows)
    for index, row in obs_data_months.iterrows():

        #remove snow melt runoff events
        if row['Pr'] == 0 or row['RO'] > row['Pr']:
            obs_data_months.drop(index = index, inplace=True)



    def get_obs_avgs(combined_df,crop1_yrs, crop2_yrs, lower_bins, upper_bins, var):
        '''
        Splits observed data into two halves for validation

        Precip and runoff events are split by crop and then binned by depth. The
        events in each bin are split and then merged together by crop so
        that each calibration and validation set has an equal number of 
        events by crop and depth
        '''

        #Split data into two different dataframes by crop type
        crop1_df = combined_df[combined_df['Year'].astype(int).isin(crop1_yrs)]
        crop2_df = combined_df[combined_df['Year'].astype(int).isin(crop2_yrs)]

        ## set bins and months
            
        #create lists that will hold avg values by bin
        val1_crop_bins = []
        val2_crop_bins = []

        for low_bin, high_bin in zip(lower_bins, upper_bins):

            #get data for month
            bins1_df = crop1_df[(crop1_df[var] >= low_bin) & (crop1_df[var] < high_bin)]

            bins2_df = crop2_df[(crop2_df[var] >= low_bin) & (crop2_df[var] < high_bin)]

            def split_bins(binned_df):
                '''
                split binned events into two halves for each crop
                '''

                #split dataframe into two equal dfs if total len is > 1
                if len(binned_df) > 1:

                    #split into two sub_dataframes (returned type is a list)
                    split_df = np.array_split(binned_df, 2)

                #create list that matches length of split dataframe if len is < 1
                if len(binned_df) < 2:
                    
                    binned_df[var] = binned_df[var].astype(float) / 2

                    split_df = [binned_df,binned_df]

                val1_crop_bins.append(split_df[0])
                val2_crop_bins.append(split_df[1])

            split_bins(bins1_df)
            split_bins(bins2_df)

        #combine events in bins
        val1_crop_recomb = pd.concat(val1_crop_bins)
        val2_crop_recomb = pd.concat(val2_crop_bins)

        return val1_crop_recomb, val2_crop_recomb
        
    #Define precip bins
    lower_pr_bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110]
    upper_pr_bins = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 300]

    #Define runoff bins
    lower_RO_bins = [0, 5, 10, 15, 25]
    upper_RO_bins = [5, 10, 15, 25, 50, 500]

    #Get outputs for two validation periods
    obs_RO_val1, obs_RO_val2 = get_obs_avgs(obs_data_months, crop1_yrs, crop2_yrs,lower_RO_bins, upper_RO_bins, 'RO')
    obs_pr_val1, obs_pr_val2 = get_obs_avgs(comb_df_sel, crop1_yrs, crop2_yrs, lower_pr_bins, upper_pr_bins, 'filled_pr')

    #Combine two validation periods for full observed dataset (used for all calibration tests)
    obs_RO_all = pd.concat([obs_RO_val1,obs_RO_val2])

    mod_df = mod_data_months.reset_index()

    def compare_mod_obs(obs_RO, obs_pr):

        ####get average runoff:precip ratio from monthly totals ###

        #Avg total monthly Pr
        avg_pr_obs = obs_pr.groupby('Month')['filled_pr'].sum() / (len(obs_rot))
        avg_pr_mod = cli_df_sel.groupby('Month')['cli_pr'].sum() / 55

        #Avg total monthly RO
        avg_RO_obs = obs_RO.groupby('Month')['RO'].sum() / (len(obs_rot))
        avg_RO_mod = mod_df.groupby('Month')['RO'].sum() / 55

        #Avg total monthly TSS
        avg_TSS_obs = obs_RO.groupby('Month')['TSS'].sum() / (len(obs_rot))
        avg_TSS_mod = mod_df.groupby('Month')['TSS'].sum() / 55

        #Runoff ratio
        obs_RR = avg_RO_obs / avg_pr_obs
        mod_RR = avg_RO_mod / avg_pr_mod

        months = [4,5,6,7,8,9,10,11]

        mean_vals = pd.DataFrame({'Month':months,\
                                  'obs_monthly_pr':avg_pr_obs, 'mod_monthly_pr':avg_pr_mod,\
                                  'obs_RO':avg_RO_obs, 'mod_RO':avg_RO_mod,\
                                  'obs_RR':obs_RR, 'mod_RR':mod_RR,\
                                  'obs_TSS':avg_TSS_obs, 'mod_TSS':avg_TSS_mod}).fillna(0)


        print(wshed)
        print(mean_vals)

        #perform nse and pbias tests on runoff ratios and total monthly runoffs
        nse_RO = float(he.evaluator(he.nse, mean_vals['mod_RO'], mean_vals['obs_RO']))
        pbias_RO = float(he.evaluator(he.pbias, mean_vals['mod_RO'], mean_vals['obs_RO']))
        nse_RR = float(he.evaluator(he.nse, mean_vals['mod_RR'], mean_vals['obs_RR']))
        pbias_RR = float(he.evaluator(he.pbias, mean_vals['mod_RR'], mean_vals['obs_RR']))
        nse_TSS = float(he.evaluator(he.nse, mean_vals['mod_TSS'], mean_vals['obs_TSS']))
        pbias_TSS = float(he.evaluator(he.pbias, mean_vals['mod_TSS'], mean_vals['obs_TSS']))

        nse_pbias_df = pd.DataFrame({'NSE_TSS':nse_TSS, 'PBIAS_TSS':pbias_TSS,\
                                     'NSE_RO':nse_RO, 'PBIAS_RO':pbias_RO,\
                                     'NSE_RR':nse_RR, 'PBIAS_RR':pbias_RR}, index=['Value'])

        print(nse_pbias_df)

        #write pr/ro/TSS values and nse/pbias outcomes to excel
        writer = pd.ExcelWriter('C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/Comparisons/NSE_PBIAS/{}_test.xlsx'.format(wshed))
        mean_vals.to_excel(writer, "RO-TSS Values", index=False)
        nse_pbias_df.to_excel(writer, "Stat Tests", index=False)
        writer.save()

        return mean_vals, nse_pbias_df

    #run compare_mod_obs using full observed dataset (or half for validation)
    avg_vals, nse_pbias_vals = compare_mod_obs(obs_RO_all, comb_df_sel)

    avg_vals_dic[wshed] = avg_vals
    nse_pbias_dic[wshed] = nse_pbias_vals
    

#create list of watershed IDs, simulated DF hillslope IDs,
# and list of directories that hold simiulated outputs
wshed_lst = ['BE1', 'DO1', 'GO1', 'RO1', 'ST1']
hillslopes = ['p221', 'p206', 'p66', 'p77', 'p154']
mod_dir_lst = ['DF_Comp3/Obs_full',\
                'DF_Comp3/Obs_full',\
                'DF_Comp3/Obs_full',\
                'DF_Comp5/Obs_full',\
                'DF_Comp/Obs_full']

#Define TSS adjustments for obs data
# = Percent of TSS Yield that is soil particulate matter (i.e. no organic matter)
#for each DF site
TSS_adjustments = [0.86, 0.81, 0.85, 0.835, 0.83]


#prep lists for mod starts, obs years, and years for each crop
lst_mod_rot_starts_wshed = [[1,2,3,4,5], 
                            [1,2,3,4,5,6,7],\
                            [1,2,3,4,5,6],\
                            [1,2,3,4,5,6],\
                            [1,2,3,4,5,6,7]]

obs_rot_yrs = [[2012,2013,2014,2015,2016],\
                [2013,2014,2015,2016,2017,2018,2019],\
                [2011,2012,2013,2014,2015,2016],\
                [2014,2015,2016,2017,2018,2019],\
                [2011,2012,2013,2014,2015,2016,2017]]

mod_cli_yrs = [[11,12,13,14,15],\
                [22,23,24,25,26,27,28],\
                [31,32,33,34,35,36],\
                [13,14,15,16,17,18],\
                [8,9,10,11,12,13,14]]

lst_crop1_yrs = [[2013,2015],\
                    [2013,2015,2017,2019],\
                    [2011,2012],\
                    [2015,2016,2017,2019],\
                    [2011,2012,2013]]

lst_crop2_yrs = [[2012,2014,2016],\
                [2014,2016,2018],\
                [2013,2014,2015,2016],\
                [2014,2018],\
                [2014,2015,2016,2017]]

avg_vals_dic = {}
nse_pbias_dic = {}

#loop through variables that correspond to the 5 watersheds
for wshed, hill, mod_dir, mod_yrs, TSS_adjusts, crop1_yrs, crop2_yrs, obs_rot, in zip(wshed_lst,\
                                                                                      hillslopes,\
                                                                                      mod_dir_lst,\
                                                                                      mod_cli_yrs,\
                                                                                      TSS_adjustments,\
                                                                                      lst_crop1_yrs,\
                                                                                      lst_crop2_yrs,\
                                                                                      obs_rot_yrs):

    #set directory paths to DF and cligen data
    obs_dir = 'E:/Soil_Erosion_Project/WEPP_PRWs/{}/obs_data/'.format(wshed)
    cli_dir = 'E:/Soil_Erosion_Project/WEPP_PRWs/{}/Runs/{}/wepp/runs/'.format(wshed,mod_dir)
    wepp_out_dir = 'E:/Soil_Erosion_Project/WEPP_PRWs/{}/Runs/{}/wepp/output/'.format(wshed,mod_dir)

    NSE_PBIAS_Analysis(obs_dir,\
                       wshed,\
                       cli_dir,\
                       wepp_out_dir,\
                       hill,\
                       mod_yrs,\
                       TSS_adjusts,\
                       crop1_yrs,\
                       crop2_yrs,\
                       obs_rot)


#Combine data across sites and get mean monthly values
avg_vals_dic['comb'] = pd.concat(avg_vals_dic.values(), ignore_index=True)
avg_vals_dic['Combined'] = avg_vals_dic['comb'].groupby('Month').mean()
avg_vals_dic['Combined']['Month'] = [4,5,6,7,8,9,10,11]

comb_df = avg_vals_dic['Combined']


def NSE_PBIAS(input_dic, obs_col, mod_col):
    '''
    calculate nse and pbias values for observed and modeled data
    and return values as floats
    '''
    nse = float(he.evaluator(he.nse, input_dic[mod_col], input_dic[obs_col]))
    pbias = float(he.evaluator(he.pbias, input_dic[mod_col], input_dic[obs_col]))

    return nse, pbias

#get NSE and PBIAS values for combined data
nse_RO_comb, pbias_RO_comb = NSE_PBIAS(comb_df, 'obs_RO', 'mod_RO')
nse_RR_comb, pbias_RR_comb = NSE_PBIAS(comb_df, 'obs_RR', 'mod_RR')
nse_TSS_comb, pbias_TSS_comb = NSE_PBIAS(comb_df, 'obs_TSS', 'mod_TSS')

#create dataframe of NSE and PBIAS values from combined data and assign to new key in nse_pbias_dic
nse_pbias_dic['Combined'] = pd.DataFrame({'NSE_TSS':nse_TSS_comb, 'PBIAS_TSS':pbias_TSS_comb,\
                                          'NSE_RO':nse_RO_comb, 'PBIAS_RO':pbias_RO_comb,\
                                          'NSE_RR':nse_RR_comb, 'PBIAS_RR':pbias_RR_comb}, index=['Value'])


import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

#Define x/y axis coordinates for each plot
subx_vals = [0,0,0,1,1,1]
suby_vals = [0,1,2,0,1,2]

def graph_comps(in_dic, x_lab, y_lab, title, out_name, comp_type, col_lab1, col_lab2, ylimit, NSE_col, PBIAS_col):
    '''
    dic1 = first dictionary input option
    dic2 = second dictionary input option
    crop_names1/2 = list of crop names
    colors1/2 = colors corresponding to crop names
    season = name of season
    title = partial title insert being assigned to output figure
    col_lab1/2 = column label for variables (different between obs and mod)
    '''

    #Set up a subplot for each watershed that contains plots for each watershed
    fig, axes = plt.subplots(nrows = 2, ncols = 3, figsize = (16, 12))

    nsepb_yvals = [1.1, 1.1, 1.1, -0.1, -0.1, -0.1]
    wshed_lst_graphing = ['BE1', 'DO1', 'GO1', 'RO1', 'ST1', 'Combined']

    #loop through watershed, crops, colors for crops, and the subplot x,y coords
    for wshed, subx, suby, nsepb_y, in \
        zip(wshed_lst_graphing, subx_vals, suby_vals,nsepb_yvals):
        
        #define x and y values
        obs_x = in_dic[wshed]['Month']
        obs_y =in_dic[wshed][col_lab1]

        mod_x = in_dic[wshed]['Month']
        mod_y = in_dic[wshed][col_lab2]

        axes[subx, suby].plot(obs_x,\
                              obs_y,\
                              marker = 'o',\
                              label = 'Discovery Farms',\
                              color = 'orange',\
                              alpha = 1)

        axes[subx, suby].plot(mod_x,\
                              mod_y,\
                              marker = 'o',\
                              label = 'WEPP',\
                              color = 'blue',\
                              alpha = 1)

        axes[subx,suby].set_xlabel(x_lab)
        axes[subx,suby].set_ylabel(y_lab)

        axes[subx,suby].set_ylim(0,ylimit)

        #Add sub-title
        axes[subx,suby].set_title('{}'.format(wshed))

        NSE = nse_pbias_dic[wshed][NSE_col]
        PBIAS = nse_pbias_dic[wshed][PBIAS_col]

        nse_pbias_txt = '\n'.join((r'$NSE = %.2f$' % (NSE, ),
                                   r'$PBIAS = %.0f$' % (PBIAS, )))


        props = dict(boxstyle='round', facecolor='grey', alpha=0.2)

        axes[subx,suby].text(0.73, nsepb_y, nse_pbias_txt, transform=axes[subx,suby].transAxes, fontsize=10,\
                             verticalalignment='top', bbox=props)

    #Add title to grouping of subplots
    fig.suptitle(title, fontsize = 14)

    #Set up figure legend items
    DF_legend = mpatches.Patch(color='orange', label='Discovery Farms Data')
    WEPP_legend = mpatches.Patch(color='blue', label='WEPP Outputs')

    fig.legend(handles=[DF_legend, WEPP_legend],loc = 'lower center')

    #save figure to comparisons folder
    fig_path = 'C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/Comparisons/Final_Graphs/{}_{}.png'.format(out_name,comp_type)
    fig.savefig(fig_path)



RO_title = "Fully Calibrated WEPP Outputs vs Discovery Farms Data: \n Average Total Monthly Runoff"
RR_title = "Fully Calibrated WEPP Outputs vs Discovery Farms Data: \n Monthly Runoff Ratios"
TSS_title = "Fully Calibrated WEPP Outputs vs Discovery Farms Data: \n Average Total Monthly Soil Loss"

RO_ylab = 'Average Total Runoff (mm)'
RR_ylab = 'Average Runoff Ratio (mm)'
TSS_ylab = 'Average Total Soil Loss (tons/ha)'

graph_comps(avg_vals_dic, 'Month', RO_ylab, RO_title, 'avgRO', 'full_cal', 'obs_RO', 'mod_RO', 15, 'NSE_RO', 'PBIAS_RO')
graph_comps(avg_vals_dic, 'Month', RR_ylab, RR_title, 'avgRR', 'full_cal', 'obs_RR', 'mod_RR', 0.15, 'NSE_RR', 'PBIAS_RR')
graph_comps(avg_vals_dic, 'Month', TSS_ylab, TSS_title, 'avgTSS', 'full_cal', 'obs_TSS', 'mod_TSS', 0.42,'NSE_TSS', 'PBIAS_TSS')
