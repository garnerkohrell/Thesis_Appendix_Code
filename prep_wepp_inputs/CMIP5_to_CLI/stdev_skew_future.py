import pandas as pd 
import numpy as np 
import os


def future_cal_stdevs_skews(top_dir,obs_dir, obs_ID, obs_loc, mod_ID, loc_ID):
    '''
    Calibrates the future precipitation stdev and skew coefficients using 
    the delta change method. The precipitation stdevs in the .TOP files generated
    with measured data already include the Discovery Farms calibration adjustments,
    so they are incorperated into the future climate files during the delta change 
    calculations

    top_dir = path to .TOP file directory

    obs_dir = path to observed datasets

    obs_ID = reference to mod from CMIP5 historically downloaded data, this was only
    used for finding the correct .TOP file that matches the location of the observed weather
    station in other scripts

    obs_loc = same as clim_mod, but referencing the location that the historically modeled datasets
    covered

    mod_ID = 

    '''

    #select files without calibrated precip stdevs or skews
    top_obs = os.path.join(obs_dir, '{}_{}_{}_19.top'.format(wshed, obs_ID, obs_loc))
    top_19 = os.path.join(top_dir, '{}_{}_{}_19.top'.format(wshed, mod_ID, loc_ID))
    top_59 = os.path.join(top_dir, '{}_{}_{}_59.top'.format(wshed, mod_ID, loc_ID))
    top_99 = os.path.join(top_dir, '{}_{}_{}_99.top'.format(wshed, mod_ID, loc_ID))

    def top_to_dic(top_file):
        '''
        Assigns data in .top file rows to dataframes
        '''
        # Read in .top file
        top_data = pd.read_csv(top_file, skiprows = 3, sep = '\s+', header=None, engine = 'python')
        Months = [1,2,3,4,5,6,7,8,9,10,11,12]

        #Create dataframe of monthly precip st dev values
        stdev_vals = top_data.drop([0,1], axis=1)
        stdev_df = pd.DataFrame({'stdev_P' : stdev_vals.loc['S'], 'Months':Months})
        stdev_df.set_index('Months', inplace =True)

        #Create dataframe of monthly precip skew values
        skew_vals = top_data.drop([0,13], axis=1)
        skewp_df = pd.DataFrame({'skew_P' : skew_vals.loc['SKEW'], 'Months':Months})
        skewp_df.set_index('Months', inplace =True)

        #Do not let skew precip values be greater than 4.5 since the Pearson III model is not robust enough to handle
        #skews greater than that
        skewp_df['skew_P'] = skewp_df['skew_P'].astype(float).clip(0,4.3)

        stats_df = pd.DataFrame({'stdev_P':stdev_df['stdev_P'], 'skew_P':skewp_df['skew_P']})

        return stats_df

    stats_obs = top_to_dic(top_obs)
    stats_19 = top_to_dic(top_19)
    stats_59 = top_to_dic(top_59)
    stats_99 = top_to_dic(top_99)

    cal_stats_59 = (stats_59 - stats_19) + stats_obs
    cal_stats_99 = (stats_99 - stats_19) + stats_obs


    # Prep create_out_string function which is used later in script after calibrated values have been calculated
    def create_out_string(df, var, var_name):
        '''
        creates string of calibrated data in .top file format
        '''

        new_line = str('{}{:.2f}  {:.2f}  {:.2f}  {:.2f}  {:.2f}  {:.2f}  {:.2f}  {:.2f}  {:.2f}  {:.2f}  {:.2f}  {:.2f}'\
                        .format(var_name, df[var].iloc[0], df[var].iloc[1], df[var].iloc[2], df[var].iloc[3], df[var].iloc[4], df[var].iloc[5],\
                                df[var].iloc[6], df[var].iloc[7], df[var].iloc[8], df[var].iloc[9], df[var].iloc[10], df[var].iloc[11]))

        return new_line

    stdev_59 = create_out_string(cal_stats_59, 'stdev_P', ' S DEV P  ')
    skew_59 = create_out_string(cal_stats_59, 'skew_P', ' SKEW P   ')
    stdev_99 = create_out_string(cal_stats_99, 'stdev_P', ' S DEV P  ')
    skew_99 = create_out_string(cal_stats_99, 'skew_P', ' SKEW P   ')


    def write_to_file(top_file,stdev_lst,skew_lst):
        '''
        Writes calibrated future stdevs and skew Ps to exisiting file
        '''
        #open .top file
        with open(top_file, 'r+') as file:
            #read lines of file
            lines = file.readlines()

            lines[4] = str(stdev_lst + '\n')
            lines[5] = str(skew_lst + '\n')

            # move file pointer to the beginning of a file
            file.seek(0)
            # truncate the file
            file.truncate()

            #write lines to truncated file
            file.writelines(lines)

            file.close()

    write_to_file(top_59,stdev_59,skew_59)
    write_to_file(top_99,stdev_99,skew_99)



wsheds = ['BE1', 'DO1', 'GO1', 'RO1', 'ST1']
BCCA_loc_IDs = [2,2,1,2,4]
LOCA_loc_IDs = [8,3,3,7,3]
methods = ['BCCA', 'BCCA', 'LOCA', 'LOCA']
mod_IDs = ['B3', 'B4', 'L3', 'L4']


# B3 = GFDL_ESM2G RCP 4.5
# B4 = GFDL_ESM2G RCP 6.0

# L3 = HadGEM2-CC RCP 4.5
# L4 = HadGEM2-CC RCP 8.5  


# loop through watershed and model reference location IDs
for wshed, BCCA_loc, LOCA_loc in zip(wsheds, BCCA_loc_IDs, LOCA_loc_IDs):

    #loop through downscaling methods and model IDs 
    for method, mod_ID in zip(methods, mod_IDs):
        
        if method == 'BCCA':
            loc_ID = BCCA_loc

        if method == 'LOCA':
            loc_ID = LOCA_loc

            obs_dir = 'C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/GDS/Obs/obs_6519/'.format(wshed)
            top_dir = 'C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/GDS/{}/'.format(wshed,method)

            future_cal_stdevs_skews(top_dir,obs_dir, 'B3', '4', 'L4', '3')