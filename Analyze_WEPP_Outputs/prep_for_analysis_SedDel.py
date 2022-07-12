def prep_data(wepp_out_dir, mod, month_start, month_end, SDR, TMDL_SD, TMDL_RO):
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


    #obs and future periods have different year lengths
    if mod == 'Obs':
        years = 55

    else:
        years = 40


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
    SD_lst = []
    RO_lst = []
    TMDL_SD_lst = []
    TMDL_RO_lst = []


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
        #multiply sed delivery value (in kg/m) by profile width to get kg,
        #convert from kg to tons,
        #divide by area to get avg soil loss in tons/ha
        #then multiply by sediment delivery ratio for watershed to get avg
        #sediment delivery to watershed

        if area > 0:
            season_df['WS_SD'] = ((((season_df['Sed-Del']) * width) * 0.00110231) / area) * SDR

            #get average total soil loss rate for hillslope and append to list
            yearly_avg_SD = season_df['WS_SD'].sum() / years 

            SD_lst.append(yearly_avg_SD)

            if yearly_avg_SD > TMDL_SD:
                TMDL_SD_lst.append(yearly_avg_SD)

        if area == 0:
            pass
        

        #remove snowmelt runoff events
        season_df = season_df[season_df['Precip'] > season_df['RO']]

        yearly_avg_RO = season_df['RO'].sum() / years

        #get average total runoff depth for hillslope and append to list
        RO_lst.append(yearly_avg_RO)

        if yearly_avg_RO > TMDL_RO:
            TMDL_RO_lst.append(yearly_avg_RO)



    #get average total sediment delivery and runoff for the entire watershed during the selected season
    SL = sum(SD_lst) / len(hillslopes)
    RO = sum(RO_lst) / len(hillslopes)

    #Get the percentage of hillslopes in a watershed above TMDL field sediment delivery
    total_TMDL_SD = (len(TMDL_SD_lst) / len(hillslopes)) * 100

    #Get the percentage of hillslopes in a watershed abvove TMDL runoff
    total_TMDL_RO = (len(TMDL_RO_lst) / len(hillslopes)) * 100

    return SD_lst, RO_lst, SL, RO, total_TMDL_SD, total_TMDL_RO