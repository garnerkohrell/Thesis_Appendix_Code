#!/usr/bin/env python
# coding: utf-8
def edit_erod_val(Ki_adj, Kr_adj ,runs_dir):
    '''
    Multiplies the interrill and rill erodibility parameters in the .sol input 
    file by the calibration adjustments for each overland flow element(OFE)

    'line 4' = Line that includes the Keff parameter for the OFE. 

    Each OFE has its own 'line 4'
    '''
    
    import os
    import pandas as pd
    import numpy as np
    
    #loop through all input files in directory
    for file_name in os.listdir(runs_dir):

        #select soil files
        if file_name.endswith('.sol'):
            file = open(str(runs_dir+file_name), "r+") # read in file 
            lines = file.readlines()  #read lines to a list

            #loop through selected lines in each file
            for num, line in enumerate(lines, 0):

                find_key = '0.750000' # Find 'Line 4' for each OFE

                if find_key in line:
                    #Get K-eff value in string with rsplit and multiply it by scale_val
                    Ki = str(round(float(line.rsplit(' ',4)[1])* Ki_adj, 6))
                    Kr = str(round(float(line.rsplit(' ',3)[1])* Kr_adj, 6))

                    print(Ki,Kr)
                    #split line by spaces and get all values except Ki and Kr
                    #Values before Ki and Kr must be separated from shear and Keff (last two in line)
                    shear_and_Keff = line.split(' ')[7::]
                    vals_before_KiKr = line.split(' ')[:-4]
                    print(shear_and_Keff)
                    print(vals_before_KiKr)
                    #rejoin the line together and separate values by spaces (no Ki or Kr included)
                    joined_shear_Keff = ' '.join(shear_and_Keff)
                    joined_before_KiKr = ' '.join(vals_before_KiKr)
                    #create new line with updated K-eff value
                    new_line = '{} {} {} {}'.format(joined_before_KiKr, Ki, Kr, joined_shear_Keff)
                    print(new_line)
                    #assign new line back to lines list
                    lines[num] = new_line

                    # move file pointer to the beginning of a file
                    file.seek(0)
                    # truncate the file
                    file.truncate()

                    #write new lines
                    file.writelines(lines)


#Example run for the Goodhue watershed in the two future periods

wshed = 'GO1'
Ki_adj = 1.35
Kr_adj = 1
scen_lst = ['CC', 'Comb', 'CT', 'NC','Per']
mod_labs = ['L3', 'L4','B3', 'B4']
period_lst = ['59','99']

#loop through future scenarios
for scen in scen_lst:
    #loop through climate models
    for mod in mod_labs:
        #loop through future periods
        for period in period_lst:

            #Define WEPP project directory
            runs_dir = 'C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/Runs/{}/{}_{}/wepp/runs/'.format(wshed,scen,mod,period)
            #run edit_Keff_val for runs directory and scale value
            edit_erod_val(Ki_adj, Kr_adj, runs_dir)


# In[ ]:




