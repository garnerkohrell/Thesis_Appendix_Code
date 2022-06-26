def analyze_cli(obs_dir, wshed, cli_dir, clim_mod, loc):
    import pandas as pd
    from scipy import stats
    import statistics
    import hydroeval as he

    #load in observed daily precipitation data
    daily_inputs = str(obs_dir + '{}_daily_MnDNR.xlsx'.format(wshed))
    daily_data_in = pd.read_excel(daily_inputs)

    #remove missing data from daily datasets
    daily_data = daily_data_in.apply(pd.to_numeric, errors='coerce')
    daily_data.fillna(0, inplace = True)

    #Define path to monthly dataset
    monthly_data = str(obs_dir + '{}_MnDNR_Obs.xlsx'.format(wshed))

    def read_excel_sheets(output_dic, monthly_data):
        """
        Read all sheets of observed precip excel file and return as dataframes
        in a dictionary

        Observed monthly pr averages should be in one sheet labeled "Monthly_pr"

        Observed monthly number of pr events should be in a separate sheet labeled
        "Monthly_pr_e"  ... _e stands for events

        Observed temperature data should be in daily format and have a separate column for 
        the month ID number (i.e. 1, 2, 3, 4...)
        """
        #Read in excel file
        xl = pd.ExcelFile(monthly_data)
        columns = None
        #loop through sheets
        for idx, name in enumerate(xl.sheet_names):

            #define excel sheet
            sheet = xl.parse(name)

            # Assume index of existing data frame when appended
            df = pd.DataFrame(sheet)

            #select sheets with monthly data
            if 'Monthly' in name:
                #set year as index
                df.set_index('Year', inplace = True)
                output_dic[name] = df

    obs_monthly_data = {}
    read_excel_sheets(obs_monthly_data, monthly_data)

    #convert data from F and inches to C and mm
    daily_data['Pr'] = daily_data['Pr'] * 25.4
    daily_data['Tmax'] = (daily_data['Tmax'] - 32) * 5.0/9.0
    daily_data['Tmin'] = (daily_data['Tmin'] - 32) * 5.0/9.0


    ### get mean total precipitation depth, precipitation depth per event, number of precip events,
    ### and max/min temperatures for every month in observed data
    MnDNR_monthly = pd.DataFrame()
    MnDNR_monthly['Pr'] = obs_monthly_data['Monthly_pr'].mean() * 25.4
    MnDNR_monthly['Pr_mean_e'] = daily_data[daily_data['Pr']>0].groupby('Month')['Pr'].mean()
    MnDNR_monthly['Pr_e'] = obs_monthly_data['Monthly_pr_e'].mean()
    MnDNR_monthly['Tmax'] = daily_data.groupby('Month')['Tmax'].mean()
    MnDNR_monthly['Tmin'] = daily_data.groupby('Month')['Tmin'].mean()


    #set up lists for appending cligen data to for each storm type
    obs_depths = []
    obs_depth_stds = []

    ## Get mean depths for different storm types using observed data
    obs_wet = daily_data[daily_data['Pr'] > 0]
    obs_depths.append(obs_wet[obs_wet['Pr'] <= 10]['Pr'].mean())
    obs_depth_stds.append(statistics.pstdev(obs_wet[obs_wet['Pr'] <= 10]['Pr']))

    obs_10 = obs_wet[obs_wet['Pr'] > 10]
    obs_depths.append(obs_10[obs_10['Pr'] <= 25]['Pr'].mean())
    obs_depth_stds.append(statistics.pstdev(obs_10[obs_10['Pr'] <= 25]['Pr']))

    obs_25 = obs_wet[obs_wet['Pr'] > 25]
    obs_depths.append(obs_25[obs_25['Pr'] <= 50]['Pr'].mean())
    obs_depth_stds.append(statistics.pstdev(obs_25[obs_25['Pr'] <= 50]['Pr']))

    obs_depths.append(obs_wet[obs_wet['Pr'] > 50]['Pr'].mean())
    obs_depth_stds.append(statistics.pstdev(obs_wet[obs_wet['Pr'] > 50]['Pr']))


    
    #Read in and prep cligen data
    cli_data = pd.read_csv(str(cli_dir + '/{}_{}_{}_19.cli'.format(wshed,clim_mod,loc)), skiprows = 13, sep = '\s+| ', engine = 'python')
    cli_data.drop([0,], axis = 0, inplace = True)
    cli_data['Pr'] = cli_data['prcp'].astype(float)
    cli_data['Month'] = cli_data['mo'].astype(int)
    cli_data['year'] = cli_data['year'].astype(int)
    cli_data['Tmax'] = cli_data['tmax'].astype(int)
    cli_data['Tmin'] = cli_data['tmin'].astype(int)

    #define months as integers in list
    months = [1,2,3,4,5,6,7,8,9,10,11,12]

    #loop through months
    for month in months:
        #calculate stdev for cligen and measured data
        stdev = statistics.pstdev((cli_data[cli_data['Month'] == month]['Pr'] / 25.4))
        stdev_obs = statistics.pstdev((daily_data[daily_data['Month'] == month]['Pr']/ 25.4))

    # get mean total precipitation depth, precipitation depth per event, number of precip events,
    # and max/min temperatures for every month
    cli_avgs = pd.DataFrame()
    cli_avgs['Pr'] = cli_data.groupby('Month')['Pr'].sum() / 55
    cli_avgs['Pr_mean_e'] = cli_data[cli_data['Pr'] > 0].groupby('Month')['Pr'].mean()
    cli_avgs['Pr_e'] = cli_data[cli_data['Pr'] > 0].groupby('Month')['Pr'].count() / 55
    cli_avgs['Tmax'] = cli_data.groupby('Month')['Tmax'].mean()
    cli_avgs['Tmin'] = cli_data.groupby('Month')['Tmin'].mean()


    #set up lists for appending cligen data to for each storm type
    cli_depths = []
    cli_depth_stds = []

    ## Get mean depths for different storm types using cligen outputs 
    cli_wet = cli_data[cli_data['Pr'] > 0]
    cli_depths.append(cli_wet[cli_wet['Pr'] <= 10]['Pr'].mean())
    cli_depth_stds.append(statistics.pstdev(cli_wet[cli_wet['Pr'] <= 10]['Pr']))

    cli_10 = cli_wet[cli_wet['Pr'] > 10]
    cli_depths.append(cli_10[cli_10['Pr'] <= 25]['Pr'].mean())
    cli_depth_stds.append(statistics.pstdev(cli_10[cli_10['Pr'] <= 25]['Pr']))

    cli_25 = cli_wet[cli_wet['Pr'] > 25]
    cli_depths.append(cli_25[cli_25['Pr'] <= 50]['Pr'].mean())
    cli_depth_stds.append(statistics.pstdev(cli_25[cli_25['Pr'] <= 50]['Pr']))

    cli_depths.append(cli_wet[cli_wet['Pr'] > 50]['Pr'].mean())
    cli_depth_stds.append(statistics.pstdev(cli_wet[cli_wet['Pr'] > 50]['Pr']))


    p_stat_lst = []

    def run_p_test(obs, cli, top_depth):
        '''
        Tests if there is a statistically significant difference between
        measured and cligen generated average precip depths for each storm 
        type using welch's p-test

        obs = observed dataframe for given storm type

        cli = cligen dataframe for given storm type

        top_depth = maximum depth range in storm type bin
        '''
        stat, p = stats.ttest_ind(obs[obs['Pr'] <= top_depth]['Pr'], cli[cli['Pr'] <= top_depth]['Pr'], equal_var = False)

        p_stat_lst.append(p)

    #light storm
    run_p_test(obs_wet,cli_wet, 10)
    #moderate storm
    run_p_test(obs_10,cli_10, 25)
    #heavy storm
    run_p_test(obs_25,cli_25, 50)

    #intense storm (not run with "run_p_test" function)
    stat, p = stats.ttest_ind(obs_wet[obs_wet['Pr'] > 50]['Pr'], cli_wet[cli_wet['Pr'] > 50]['Pr'], equal_var = False)
    p_stat_lst.append(p)
    

    #Create dataframe with obs/cligen mean depths, stdevs, and p-values for each storm type
    storm_types = ['Light', 'Moderate', 'Heavy', 'Intense']
    binned_storm_depths = pd.DataFrame({'Storm Type':storm_types, 'Measured Mean Depth':obs_depths, 'Measured StDev':obs_depth_stds,\
                                        'Cligen Mean Depth': cli_depths, 'Cligen StDev':cli_depth_stds, 'p value':p_stat_lst})
    


    def run_nse_rmse(var):
        '''
        Compares measured monthly variables with cligen simulated monthly variables
        using NSE and RMSE tests

        var = variable being compared with NSE and RMSE tests
        '''
        nse = he.evaluator(he.nse, cli_avgs[var], MnDNR_monthly[var])
        rmse = he.evaluator(he.rmse, cli_avgs[var], MnDNR_monthly[var])

        return nse,rmse


    # Define list of variables for input into run_nse_pbias
    var_lst = ['Pr', 'Pr_mean_e', 'Pr_e', 'Tmax', 'Tmin']

    #lists to hold outputs from NSE and RMSE tests for each variable
    nse_lst = []
    rmse_lst = []

    #loop through variables
    for var in var_lst:

        #run nse and RMSE tests for variable in loop iteration
        nse,rmse = run_nse_rmse(var)

        #append to corresponding lists
        nse_lst.append(nse)
        rmse_lst.append(rmse)

    #create dataframe of NSE and RMSE outputs by climate variable
    nse_rmse_df = pd.DataFrame({'clim_var':var_lst, 'NSE':nse_lst, 'rmse':rmse_lst})

    # Return measured monthly averages, cligen monthly averages, nse and rmse values comparing measured 
    # and cligen monthly averages and the measured and cligen generated binned storm depths 
    # along with their p-test comparisons

    return MnDNR_monthly, cli_avgs, nse_rmse_df, binned_storm_depths



import pandas as pd

wsheds = ['BE1', 'DO1', 'GO1', 'RO1', 'ST1']

#Define location IDs for each cligen baseline file
mod_loc_IDs = [[2,2,8,8],\
               [2,2,3,3],\
               [1,1,3,3],\
               [2,2,7,7],\
               [4,4,3,3]]


obs_loc_IDs = [2,2,1,2,4]

mod_IDs = ['B3', 'B4', 'L3', 'L4']


def export_comps_vals(cli_input_dir, cli_input_ID): 
    '''
    Exports the measured and cligen generated monthly averages, binned storm depth comparisons, and
    nse/rmse test outputs.

    cli_input_dir = name of directory holding cligen generated data input. This variable can be 
    the cligen outputs generated with the MnDNR measured data, or the cligen outputs generated 
    with the CMIP5 historically modeled data

    cli_input_ID = uncal for CMIP5 historically modeled data and 'cal' 
    '''

    for wshed, mod_loc_lst, obs_loc_ID in zip(wsheds, mod_loc_IDs,obs_loc_IDs):

        #set up directories with measured datasets and cligen outputs
        obs_dir = 'C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/obs_data/'.format(wshed)
        cli_dir = 'C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/{}/PAR/'.format(wshed,cli_input_dir)

        for mod, loc in zip(mod_IDs,mod_loc_lst):

            #run analyze_cli for function inputs
            MnDNR_df, cli_df, nse_rmse_df, binned_storms_df = analyze_cli(obs_dir, wshed, cli_dir, mod, loc)

            #output to excel
            MnDNR_df.to_excel('C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/cligen_comparisons/{}_MnDNR.xlsx'.format(wshed))
            cli_df.to_excel('C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/cligen_comparisons/{}_cligen.xlsx'.format(wshed))
            nse_rmse_df.to_excel('C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/cligen_comparisons/{}_nse_rmse.xlsx'.format(wshed))
            binned_storms_df.to_excel('C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/cligen_comparisons/{}_binned_storms.xlsx'.format(wshed))
