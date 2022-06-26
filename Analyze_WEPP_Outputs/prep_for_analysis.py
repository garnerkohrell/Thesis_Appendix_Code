def prep_data(cli_dir, wepp_out_dir, mod, month_start, month_end):
    '''
    Loads in wepp output data from .ebe and .loss files. Extracts Sediment
    delivery and runoff values from .ebe and then converts sed-del values to 
    a mass/area soil loss value using profile width and area values extracted 
    from the .loss files.

    Also loads in precip data from a .cli cligen file. 1 cligen file per watershed

    wepp_out_dir = WEPP watershed/scenario/clim model output directory 

    cli_dir = directory with cli file (wepp input directory - only one file is loaded in)

    mod = climate model scenario

    month_start = integer value of month at beginning of season selection

    month_start = integer value of month at end of season selection
    '''

    import pandas as pd
    import os

    ######## Load in .cli files and prep precip data #########


    #get cli files from input/cli directory, but only select one 
    cli_files = [x for x in os.listdir(cli_dir) if x.endswith('.cli')]
    cli_file = str(cli_dir + cli_files[1])

    #read in first cligen file. The .cli files are constant across hillslopes
    cli_df = pd.read_csv(cli_file, skiprows = 13, sep = '\s+| ', engine = 'python')
    cli_df.drop([0,], axis = 0, inplace = True)
    cli_df.reset_index(inplace = True)

    #convert columns to floats
    cli_df['Year'] = cli_df['year'].astype(int)
    cli_df['Day'] = cli_df['da'].astype(int)
    cli_df['Month'] = cli_df['mo'].astype(int)
    cli_df['cli_pr'] = cli_df['prcp'].astype(float)
    cli_df['st_dur'] = cli_df['dur'].astype(float)
    cli_df['cli_tmax'] = cli_df['tmax'].astype(float)
    cli_df['cli_tmin'] = cli_df['tmin'].astype(float)
    cli_df['cli_tavg'] = (cli_df['cli_tmax'] + cli_df['cli_tmin']) / 2

    #Find average precip intensity
    cli_df['pri'] = (cli_df['cli_pr']) / cli_df['st_dur']
    cli_df['pri'] = cli_df['pri'].fillna(0)

    #obs and future periods have different year lengths
    if mod == 'Obs':
        years = 55

    else:
        years = 40


    #select months in season
    seasonal_cli = cli_df[cli_df['mo'].astype(int) >= month_start] 
    seasonal_cli = seasonal_cli[seasonal_cli['mo'].astype(int) <= month_end]


    #Find number of days where precip > 25mm (seasonal and growing season)
    pr_25 = round(((seasonal_cli['cli_pr'][seasonal_cli['cli_pr'] > 25].count()) / years), 1)

    #Find average precip intensity for all storm events
    avg_pri= round((seasonal_cli['pri'][seasonal_cli['pri'] != 0].mean()), 1)

    #Find average total seasonal and growing season precip 
    avg_pr = round(((seasonal_cli['cli_pr'].sum()) / years), 1)

    avg_dur = round(seasonal_cli['st_dur'].mean(), 1)

    #Find average total max/min temperatures
    avg_tmax = round(seasonal_cli['cli_tmax'].mean(), 1)
    avg_tmin = round(seasonal_cli['cli_tmin'].mean(), 1)

    print(avg_tmax)



    #precip events to list for seasonal
    PR_lst = seasonal_cli['cli_pr'].to_list()



    ##### Load in .ebe and .loss files ######

    #get ebe files from output directory
    hillslopes = [x for x in os.listdir(wepp_out_dir) if x.endswith('.ebe.dat')]

    #define column names for ebe file load in
    ebe_col_list = ['Day', 'Month', 'Year', 'Precip', 'RO', 'IR-det',\
                    'Av-det', 'Mx-det', 'Point', 'Av-dep', 'Mx-dep',\
                    'Point_2', 'Sed-Del', 'ER']



    #get loss files from output directory
    loss_files = [x for x in os.listdir(wepp_out_dir) if x.endswith('.loss.dat')]


    #output list that will hold all soil loss and runoff values for each hillslope
    SL_lst = []
    RO_lst = []
    PR_R_lst = []
    PRi_R_lst = []

    ##### Prep data for graphing ######

    #loop through all .loss and .ebe files (i.e. loop through hillslopes in watershed)
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

        ### select data by season ###

        #select months in season
        season_df = all_data[all_data['Month'] >= month_start] 
        season_df = season_df[season_df['Month'] <= month_end]

        #extract individual hill loss data
        #multiple sed delivery value (in kg/m) by profile width to get kg,
        #convert from kg to tons,
        #divide by area to get avg soil loss in tons/ha

        if area > 0:
            season_df['soil_loss'] = (((season_df['Sed-Del']) * width) * 0.00110231) / area

            #get average total soil loss rate for hillslope and append to list
            yearly_avg_SL = season_df['soil_loss'].sum() / years 

            SL_lst.append(yearly_avg_SL)

        if area == 0:
            pass
        

        #remove snowmelt runoff events
        season_df = season_df[season_df['Precip'] > season_df['RO']]

        #get average total runoff depth for hillslope and append to list
        RO_lst.append((season_df['RO'].sum() / years))

        #extend individual precipitation depths associated with runoff events to list
        PR_R_lst.extend(season_df['Precip'].to_list())

        merged_df = pd.merge(seasonal_cli, season_df, how = 'right', on = ['Day', 'Month','Year'])

        #extend individual precipitation intensities associated with runoff events to list
        PRi_R_lst.extend(merged_df['pri'].tolist())

    #get average total soil loss and runoff for the entire watershed during the selected season
    SL = sum(SL_lst) / len(hillslopes)
    RO = sum(RO_lst) / len(hillslopes)

    return SL_lst, RO_lst, PR_R_lst, PRi_R_lst, cli_df['cli_pr'], cli_df['pri'], RO, SL, avg_pr, avg_pri, pr_25, avg_dur, avg_tmax, avg_tmin