def edit_erod_val(Ki_adj, Kr_adj ,runs_dir):
    '''
    Multiplies the interrill and rill erodibility parameters in the .sol input 
    file by the calibration adjustments for each overland flow element(OFE)

    'line 4' = Line that includes the Keff parameter for the OFE. 

    Each OFE has its own 'line 4'
    '''
    
    import os
    
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
                    #Get erodibility values in string with rsplit and multiply it by corresponding adjustment
                    Ki = str(round(float(line.rsplit(' ',4)[1])* Ki_adj, 6))
                    Kr = str(round(float(line.rsplit(' ',3)[1])* Kr_adj, 6))

                    print(Ki,Kr)
                    #split line by spaces and get all values except Ki and Kr
                    #Values before Ki and Kr must be separated from shear and Keff (last two in line)
                    shear_and_Keff = line.split(' ')[7::]
                    vals_before_KiKr = line.split(' ')[:-4]
                    #rejoin the line together and separate values by spaces (no Ki or Kr included)
                    joined_shear_Keff = ' '.join(shear_and_Keff)
                    joined_before_KiKr = ' '.join(vals_before_KiKr)
                    #create new line with updated K-eff value
                    new_line = '{} {} {} {}'.format(joined_before_KiKr, Ki, Kr, joined_shear_Keff)
                    #assign new line back to lines list
                    lines[num] = new_line

                    # move file pointer to the beginning of a file
                    file.seek(0)
                    # truncate the file
                    file.truncate()

                    #write new lines
                    file.writelines(lines)


#Example run for the Goodhue watershed perennial scenarios

wshed = 'GO1'
Ki_adj = 1.35
Kr_adj = 1
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
        #run edit_erod_val for runs directory and adjustments
        edit_erod_val(Ki_adj, Kr_adj, runs_dir)