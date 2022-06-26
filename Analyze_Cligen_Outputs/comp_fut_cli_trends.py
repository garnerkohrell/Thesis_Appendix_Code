#Read in and prep cligen data
import pandas as pd 
import numpy as np

def comp_trends(wshed, method, clim_mod, loc, obs_mod, obs_loc):

    uncal_dir = 'C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/Uncalibrated/PAR/'.format(wshed)
    cal_obs_dir = 'C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/PAR/Obs/obs_6519/'.format(wshed)
    cal_fut_dir = 'C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/PAR/{}/'.format(wshed,method)

    seasonal_dic = {}
    storm_dic = {}

    def extract_cli_vars(cli_dir,period,cal_uncal,mod,loc_ID, years):

        cli_data = pd.read_csv(str(cli_dir + '/{}_{}_{}_{}.cli'.format(wshed,mod,loc_ID,period)), skiprows = 13, sep = '\s+| ', engine = 'python')
        cli_data.drop([0,], axis = 0, inplace = True)
        cli_data['Pr'] = cli_data['prcp'].astype(float)
        cli_data['Month'] = cli_data['mo'].astype(int)
        cli_data['year'] = cli_data['year'].astype(int)
        cli_data['Tmax'] = cli_data['tmax'].astype(float)
        cli_data['Tmin'] = cli_data['tmin'].astype(float)
        cli_data['dur'] = cli_data['dur'].astype(float)
        cli_data['int'] = cli_data ['Pr'] / cli_data['dur']



        #get means of cligen climate variables
        cli_avgs = pd.DataFrame()

        winter = cli_data[cli_data['Month'].isin([1,2,12])]
        spring = cli_data[cli_data['Month'].isin([3,4,5])]
        summer = cli_data[cli_data['Month'].isin([6,7,8])]
        fall = cli_data[cli_data['Month'].isin([9,10,11])]

        Pr_lst = []
        Pr_mean_lst = []
        Pr_25_lst = []
        Tmax_lst = []
        Tmin_lst = []

        for season in [winter,spring,summer,fall]:
            Pr_lst.append(season[season['Pr'] > 0]['Pr'].sum() / years)
            Pr_mean_lst.append(season[season['Pr'] > 0]['Pr'].mean())
            Pr_25_lst.append(season[season['Pr'] > 25]['Pr'].count())
            Tmax_lst.append(season['Tmax'].mean())
            Tmin_lst.append(season['Tmin'].mean())


        seasonal_df = pd.DataFrame({'Pr':Pr_lst, 'Pr_mean_e':Pr_mean_lst, 'Pr_25':Pr_25_lst, 'Tmax':Tmax_lst, 'Tmin':Tmin_lst})

        if wshed == 'RO1':
            print(seasonal_df)
            seasonal_df


        cli_depths = []
        cli_int = []

        ## separate data into storm types and then get average depth and intensity for each
        cli_wet = cli_data[cli_data['Pr'] > 0]
        cli_0_10 = cli_wet[cli_wet['Pr'] <= 10]
        cli_0_10_int = cli_0_10['Pr'] / cli_0_10['dur']

        cli_10 = cli_wet[cli_wet['Pr'] > 10]
        cli_10_25 = cli_10[cli_10['Pr'] <= 25]
        cli_10_25_int = cli_10_25['Pr'] / cli_10_25['dur']

        cli_25 = cli_wet[cli_wet['Pr'] > 25]
        cli_25_50 = cli_25[cli_25['Pr'] <= 50]
        cli_25_50_int = cli_25_50['Pr'] / cli_25_50['dur']

        cli_50p = cli_wet[cli_wet['Pr'] > 50]
        cli_50p_int = cli_50p['Pr'] / cli_50p['dur']


        cli_depths.append(cli_0_10['Pr'].mean())
        cli_depths.append(cli_10_25['Pr'].mean())
        cli_depths.append(cli_25_50['Pr'].mean())
        cli_depths.append(cli_50p['Pr'].mean())


        cli_int.append(cli_0_10_int.mean())
        cli_int.append(cli_10_25_int.mean())
        cli_int.append(cli_25_50_int.mean())
        cli_int.append(cli_50p_int.mean())


        binned_storms = pd.DataFrame({'Avg Depth (mm)':cli_depths, 'Avg Intensity (mm/hr)':cli_int})

        seasonal_dic['{}_{}'.format(cal_uncal,period)] = seasonal_df
        storm_dic['{}_{}'.format(cal_uncal,period)] = binned_storms

    #run extract_cli_vars for calibrated and uncalibrated inputs
    extract_cli_vars(cal_obs_dir, 19, 'cal', obs_mod, obs_loc, 55)
    extract_cli_vars(uncal_dir, 19, 'uncal', clim_mod, loc, 55)
    extract_cli_vars(cal_fut_dir, 59, 'cal', clim_mod, loc, 40)
    extract_cli_vars(uncal_dir, 59, 'uncal', clim_mod, loc, 40)
    extract_cli_vars(cal_fut_dir, 99, 'cal', clim_mod, loc, 40)
    extract_cli_vars(uncal_dir, 99, 'uncal', clim_mod, loc, 40)

    pear_lst_59 = []
    pear_lst_99 = []


    def calc_trends_diff(dic):

        #get % difference between periods (full dataframe calculations)
        cal_59_19 = ((dic['cal_59'] - dic['cal_19']) / abs(dic['cal_19'])) * 100
        cal_99_19 = ((dic['cal_99'] - dic['cal_19']) / abs(dic['cal_19'])) * 100

        uncal_59_19 = ((dic['uncal_59'] - dic['uncal_19']) / abs(dic['uncal_19'])) * 100
        uncal_99_19 = ((dic['uncal_99'] - dic['uncal_19']) / abs(dic['uncal_19'])) * 100

        #loop through variables and run pearson's correlation test
        for var in var_lst:
            pear_59 = np.corrcoef(cal_59_19[var], uncal_59_19[var])
            pear_99 = np.corrcoef(cal_99_19[var], uncal_99_19[var])

            #append to corresponding list
            pear_lst_59.append(pear_59[0,1])
            pear_lst_99.append(pear_99[0,1])

    #set up lists for function
    pear_lst_59 = []
    pear_lst_99 = []
    var_lst = ['Pr', 'Pr_mean_e', 'Pr_25', 'Tmax', 'Tmin']

    calc_trends_diff(seasonal_dic)

    #create output df of pearson coefficients
    stats_df = pd.DataFrame({'Variable':var_lst,'P_CO 19v59':pear_lst_59, 'P_CO 19v99':pear_lst_99})

    return stats_df

    

wsheds = ['BE1', 'DO1', 'GO1', 'RO1', 'ST1']
mod_loc_IDs = [[2,2,8,8],\
               [2,2,3,3],\
               [1,1,3,3],\
               [2,2,7,7],\
               [4,4,3,3]]

obs_loc_IDs = [2,2,1,2,4]

methods = ['BCCA', 'BCCA', 'LOCA', 'LOCA']
mod_IDs = ['B3', 'B4', 'L3', 'L4']

df_lst = []

for wshed, mod_loc_lst, obs_loc_ID in zip(wsheds, mod_loc_IDs,obs_loc_IDs):
    for mod, method, loc in zip(mod_IDs,methods,mod_loc_lst):
        df_lst.append(comp_trends(wshed, method, mod, loc, 'B3', obs_loc_ID))

output_df = pd.concat(df_lst, axis = 0)

output_df.to_excel('C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/pearson_coeff_tests.xlsx')




