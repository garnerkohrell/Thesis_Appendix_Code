def cal_stdev_skew(obs_dir, wshed, data_len, stdev_adjs, top_path, clim_mod, loc):
    '''
    Generates monthly precipitation stdevs and skew coefficient parameters using
    observed/measured data from the National Weather Service and MnDNR. The stdev
    adjustments from the Discovery Farms calibration process are then implemented into
    the stdev values. 
    
    The stdev and skew coefficeint parameters are then used to overwrite the parameters
    in the .TOP file that was initially loaded in. 


    obs_dir = path to observed datasets

    wshed = watershed ID

    data_len = string used to daily observed dataset

    stdev_adjs = standard deviation adjustments from calibration period
    top_path = path to .TOP files

    clim_mod = reference to mod from CMIP5 historically downloaded data, this was only
    used for finding the correct .TOP file that matches the location of the observed weather
    station in other scripts

    loc = same as clim_mod, but referencing the location that the historically modeled datasets
    covered
    '''

    import pandas as pd
    import statistics

    #Create path to monthly data
    daily_input = str(obs_dir + '{}_daily_MnDNR{}.xlsx'.format(wshed,data_len))

    #read in daily observed data from MnDNR
    daily_mndnr_data = pd.read_excel(daily_input)
    months = [1,2,3,4,5,6,7,8,9,10,11,12]

    stdevs = []
    skewps = []

    #loop through month and get standard deviation and skew coeff for precip
    for month,stdev_adj in zip(months,stdev_adjs):
        #selected data that only corresponds to 'month'
        data_for_month = daily_mndnr_data[daily_mndnr_data['Month'] == month]

        pr_for_month = pd.to_numeric(data_for_month['Pr'], errors='coerce')

        pr_for_month.dropna(inplace = True)
        
        #calculate stdev for month
        stdev = float(statistics.pstdev(pr_for_month))

        #add stdev adjustment from Discovery Farms calibration
        stdev_adjusted = stdev + stdev_adj

        #calculate skew coefficient for month
        skewp = pr_for_month.skew(axis = 0, skipna = True)

        #Do not let skew precip values be greater than 4.5 since the Pearson III model
        #is not robust enough to handle skews greater than that (see Cligen Documentation)
        if skewp > 4.3:
            skewp = 4.3

        skewps.append(skewp)
        stdevs.append(stdev_adjusted)

    print(skewps)
    print(stdevs)


    # Prep create_out_string function which is used later in script after calibrated values have been calculated
    def create_out_string(var, var_name):
        '''
        creates string of calibrated data in .TOP file format
        '''

        new_line = str('{}{:.2f}  {:.2f}  {:.2f}  {:.2f}  {:.2f}  {:.2f}  {:.2f}  {:.2f}  {:.2f}  {:.2f}  {:.2f}  {:.2f}'\
                        .format(var_name, var[0], var[1], var[2], var[3], var[4], var[5],\
                                var[6], var[7], var[8], var[9], var[10], var[11]))

        return new_line

    new_stdevs = create_out_string(stdevs, ' S DEV P  ')
    new_skewps = create_out_string(skewps, ' SKEW P   ')

    top_file = '{}_{}_{}_19.top'.format(wshed,clim_mod,loc)

    #open .top file
    with open(str(top_path + top_file), 'r+') as file:
        #read lines of file
        lines = file.readlines()

        lines[4] = str(new_stdevs + '\n')
        lines[5] = str(new_skewps + '\n')

        # move file pointer to the beginning of a file
        file.seek(0)
        # truncate the file
        file.truncate()

        #write lines to truncated file
        file.writelines(lines)

        file.close()


BE1_stdev_adjs = [0, 0, 0, 0.07, 0.08, 0, 0, 0, 0, 0.08, 0, 0]
DO1_stdev_adjs = [0, 0, 0, 0.04, -0.18, 0.1, 0.47, 0, 0, -0.04, 0, 0]
GO1_stdev_adjs = [0, 0, 0, 0.13, -0.07, 0, -0.16, 0, 0, 0, 0, 0]
RO1_stdev_adjs = [0, 0, 0, -0.07, 0.04, 0.03, 0.23, -0.16, -0.05, 0.07, 0, 0]
ST1_stdev_adjs = [0, 0, 0, -0.05, 0.17, 0.12, 0, 0.18, 0, 0, 0, 0]


#Goodhue (GO1) watershed shown as an example

wshed = 'GO1'

obs_dir = 'C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/obs_data/'.format(wshed)
top_path = 'C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/GDS/Obs/obs_6519/'.format(wshed)

cal_stdev_skew(obs_dir, wshed, '', ST1_stdev_adjs, top_path, 'B3', '1')