def edit_Keff_val(scale_val,runs_dir):
    '''
    Multiplies the Keff parameter in the .sol input file by the calibration 
    adjustment (scale_val) for each overland flow element(OFE)

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
                    Keff = str(round(float(line.rsplit(' ',1)[1])* scale_val, 2))
                    #split line by spaces but dont include the last value (i.e. K-eff)
                    split_line = line.split(' ')[:-1]
                    #rejoin the line together and separate values by spaces (no K-eff included)
                    joined_noKeff = ' '.join(split_line)
                    #create new line with updated K-eff value
                    new_line = str(joined_noKeff + ' ' + Keff + '\n')
                    #assign new line back to lines list
                    lines[num] = new_line

            # move file pointer to the beginning of a file
            file.seek(0)
            # truncate the file
            file.truncate()

            #write new lines
            file.writelines(lines)


#Example for the Goodhue watershed for the two future periods

wshed = 'GO1'
scale_val = 3
scen_lst = ['Per_0', 'Per_m20', 'Per_B', 'Per_p20']
mod_labs = ['B3_59', 'B3_99', 'B4_59', 'B4_99',\
           'L3_59', 'L3_99', 'L4_59', 'L4_99',\
           'Obs']

#loop through climate models
for mod in mod_labs:
    
    #loop through management scenarios
    for scen in scen_lst:

        #Define WEPP project directory
        runs_dir = 'C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/New_Runs/{}_{}/{}/wepp/runs/'.format(wshed,mod,scen)
        
        #run edit_Keff_val for runs directory and scale value
        edit_Keff_val(scale_val, runs_dir)