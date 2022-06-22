#!/usr/bin/env python
# coding: utf-8

# In[3]:

def netcdf_to_GDS(netcdf_dir, var_cols, proj_names, num_locs, proj_num, dwnsc_type, GDS_out_path):
    '''
    Extracts netcdf climate data from .nc files to workable dataframes 
    and then converts dataframes to GDS format

    netcdf_dir = path to directory that has extraction_"var".nc files
    var_cols = column names of variables (bcca and loca have different names)
    proj_names = path to text file with climate projection names
    num_locs = number of climate locations (modeled areas)
    proj_num = number of projections/models in netcdf
    '''
    
    import pandas as pd
    import numpy as np 
    import xarray as xr
    import os
    
    def netCDF_to_dic():
        '''
        Extracts netCDF data to dictionary of dataframes, creates necessary edits
        and adjustments to dataframes, and then exports to dataframes to text files
        
        Each netcdf file represents one climate variable and each of the files are
        multi-varible (i.e. they include time, location, and model projection for each
        data point)
        '''
        
        os.chdir(netcdf_dir)
        
        ## Load netCDF files into a list
        nc_files = [x for x in os.listdir('.') if x.endswith('.nc')]

        def divide_lst(lst,n):
            '''
            divide nc_files list into groups of "n"
            '''
            for i in range(0, len(lst), n):
                yield lst[i:i + n]

        nc_sep_list = list(divide_lst(nc_files,3))


        ## Convert netCDF datasets to dataframes
        netcdf_dic = {}
        #loop through netcdf files
        for lst in nc_sep_list:
            #create keys for each HUC12/method combonation
            dic_name = str(lst[0][0:5])
            netcdf_dic[dic_name] = {}
            #loop through variables in netcdf files
            for nc in lst:
                #use xr.open_dataset to open netcdf file in python
                nc_var = xr.open_dataset(nc)
                netcdf_dic[dic_name][str(nc[6::])] = nc_var.to_dataframe()


        ## Merge variables into one dataframe
        merged_dic = {} 

        def merge_cols(d, new_dic):
            '''
            Merge the pr, tmax, and tmin dataframes together into dictionary
            '''
            for dic in d:
                joined = pd.merge(d[dic]['pr.nc'], d[dic]['tasmax.nc'], on = var_cols)
                new_dic[dic] = pd.merge(joined, d[dic]['tasmin.nc'], on = var_cols)

        merge_cols(netcdf_dic, merged_dic)


        def index_to_col(d):
            '''
            Make lat, lon, proj, and time indices into columns
            cols = column key names for downscaling method
            '''
            for key in d:
                d[key] = d[key].reset_index(level=var_cols)

        index_to_col(merged_dic)


        ## Convert date/time columns into GDS format
        def edit_date_col(d):
            '''
            convert date/time columns into GDS format
            '''
            for key in d:
                d[key].time = d[key].time.astype(str).str[2:10]
                d[key].time = d[key].time.astype(str).replace('(-)', '', regex=True)

        edit_date_col(merged_dic)

        #specify if the number of climate models being used is greater than 1
        #If it is, then the dataframes have to be separated by model projections
        if proj_num > 1:
            ## Split site dataframes into separate dataframes   
            proj_dict = {}

            def split_proj(d, new_dic):
                '''
                Split site dataframes into separate dataframes by projection and assign them to
                a new dictionary (Dictionary order is: LOCA->Site->projection)
                '''
                for df in d:
                    new_dic[df] = {k: v for k, v in d[df].groupby('projection')}

            split_proj(merged_dic, proj_dict)


            ## Rename dictionary keys and projection columns
            renamed_dic = {}

            def rename_keys(names, dic, new_dic):
                '''
                rename dictionary keys and projection columns
                '''
                for df in dic:
                    new_dic[df] = dict(zip(names, list(dic[df].values())))

            proj_list = open(proj_names, 'r')
            proj_name_list = [line.rstrip('\n') for line in proj_list.readlines()]

            ### Run rename_keys for each dictionary
            rename_keys(proj_name_list, proj_dict, renamed_dic)


        ## Split dataframes by location if there are multiple locations
        if num_locs > 1:
            sep_loc_dic = {}

            def sep_by_loc(d, new_dic, end):
                '''
                seperate the LOCA and BCCA dataframes by locations
                '''
                for key in d:
                    for proj in d[key]:
                        grouped_df = d[key][proj].groupby([var_cols[1], var_cols[0]])

                        for (new_key,item),i in zip(grouped_df, range(1,end)):
                            new_dic[str(key)[0:3] + '_' + proj + '_' + str(i)] = grouped_df.get_group(new_key)


            sep_by_loc(renamed_dic, sep_loc_dic, num_locs) 
        
        #Assign finished dictionary to output dictionary based on
        #whether they have more than 1 projection and/or location
        if proj_num > 1 and num_locs >1:
            output_dic = sep_loc_dic

        if proj_num > 1 and num_locs <=1:
            output_dic = renamed_dic

        if proj_num == 1 and num_locs == 1:
            output_dic = merged_dic

        return output_dic

    #Create dictionaries of workable dataframes for each downscaling method
    prep_dic = netCDF_to_dic()

    #Reset index key for easier indexing in future functions
    for key in prep_dic:
        prep_dic[key].reset_index(inplace = True)
        
        
        
        
    
    def to_GDS_file(input_dic):
        '''
        Formats dataframes in prep_dic to GDS format and downloads them to 
        text files
        
        input_dic = output_dic from netCDF_to_dic function
        '''
        def sep_by_period(dic, new_dic):
            '''
            separate dataframes by time periods
            '''
            for key in dic:
                new_dic[key + '_19'] = dic[key].loc[0:20087]
                new_dic[key + '_59'] = dic[key].loc[20088:34697]
                new_dic[key + '_99'] = dic[key].loc[34698:49308]

        sep_dic = {}
        sep_by_period(input_dic, sep_dic)

        if dwnsc_type == 'BCCA':
            # rename lon and lat columns in BCCA to match with LOCA columns
            for df in sep_dic:
                sep_dic[df] = sep_dic[df].rename(columns={'longitude': 'lon'})
                sep_dic[df] = sep_dic[df].rename(columns={'latitude' : 'lat'})


        def coord_360to180(d):
            '''
            Convert longitude values from 360 degree format to 180 degree format
            and remove "-" in front of the value
            '''
            for key in d:
                d[key].lon = d[key].lon - 360
                d[key].lon = d[key].lon.astype(str).replace('(-)', '', regex=True)
                d[key].lon = d[key].lon.astype(float)

        coord_360to180(sep_dic)

        
        def dd_to_dms(dd):
            '''
            Convert degree decimal coordinates to DMS format

            Function is used in coord_to_dict function
            
            dd = decimal degrees
            '''
            #Use divmod to calculate DMS from dd
            #First value = quotient of numbers,
            #Second value = remainder of the quotient
            mnt,sec = divmod(dd*3600,60)
            deg, mnt = divmod(mnt,60)

            #If minute value is less than 10, then a zero must go before it
            #so that the spacing and values are correct
            if mnt >= 10:
                    deg = str('0' + str(deg)[:2])
                    mnt = str(mnt)[:2]
                    return deg+mnt

            elif mnt <10:
                    deg = str('0' + str(deg)[:2])
                    mnt = str('0' + str(mnt)[:1])
                    return deg+mnt


        def coord_to_dict(d, new_lat, new_lon):
            '''
            Create a dictionary of the lat/lon values in DMS format
            for each GPS coordinate
            '''
            for key in d:
                new_lat[key] = dd_to_dms(d[key].lat.iloc[1])
            for key in d:
                new_lon[key] = dd_to_dms(d[key].lon.iloc[1])

        ## Create empty dictionaries for new lat and lon values
        lat_values = {}
        lon_values = {}        

        coord_to_dict(sep_dic, lat_values, lon_values)


        ### Drop unneeded columns
        columns_drop = ['projection', 'lat', 'lon']
        for df in sep_dic:
            sep_dic[df].drop(columns_drop, axis=1, inplace=True)


        def reorder_col(d):
            '''
            Reorder columns to fit GDS format
            '''
            order = ['time', 'tasmax', 'tasmin', 'pr']
            for key in d:
                d[key] = d[key].reindex(columns = order)

        reorder_col(sep_dic)


        def round_vals(d):
            '''
            Round values in tmax, tmin, and pr columns to 2 decimal places
            '''
            for key in d:
                d[key] = d[key].round(decimals=1)

        round_vals(sep_dic)

        
        def remove_low_pr(d):
            '''
            Low precip events are removed to increase cligen's accuracy when
            predicting the monthly/daily probability of precip 
            '''
            for key in d:
                d[key]['pr'] = d[key]['pr'].replace(0.1, 0)
                d[key]['pr'] = d[key]['pr'].replace(0.2, 0)
                d[key]['pr'] = d[key]['pr'].replace(0.3, 0)

        remove_low_pr(sep_dic)

        
        #Create empy dictionaries for ID strings
        ID_strings = {}

        #Create dictionary of elevation values by site
        elev_dic = {'BE1':'299','DO1':'388', 'GO1':'336',\
                    'RO1':'462', 'ST1':'402'}

        #ID strings at top of GDS files require specific number of spaces
        #between country/site ID and lat/lon/elevation values
        spaces = str('                                   ')

        def Create_top_info(d, new_dic, lat_vals, lon_vals):
            '''
            Create string with site, file name, lat, lon, and elev IDs
            and assign to keys in dictionary
            '''
            for key in d:
                for k in elev_dic:
                    if key.startswith(k):
                        elev = elev_dic[k]
                        new_dic[key] = (str('99048') + key + spaces + lat_vals[key] + str('  ') + lon_vals[key] + elev)

        Create_top_info(sep_dic,ID_strings, lat_values, lon_values)


        #Create new file for each dataframe and write ID strings to the first line followed
        #by the climate data in GDS format
        for df, ID in zip(sep_dic, ID_strings):
            with open(str(GDS_out_path + df + '.txt'), 'w+') as file:
                lines = file.readlines()

                df = sep_dic[df]

                new_lines = ['{}{}  {}  {}'.format(date, str(tmax)[0:5], str(tmin)[0:5], str(pr)[0:5]) \
                                                   for date, tmax, tmin, pr in \
                                                   zip(df['time'], df['tasmax'], df['tasmin'], df['pr'])]

                file.writelines(str(ID_strings[ID])+'\n')
                for new_line in new_lines:
                    file.writelines(str(new_line)+'\n')

    #Run to_GDS_file function                
    to_GDS_file(prep_dic)

