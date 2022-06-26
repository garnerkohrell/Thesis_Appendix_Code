
def adjust_residue_CsvT(parent, file_type):
    '''
    Function that scans a directory to find a specific file type 
    (.man in this case). Once the file type is located, the function
    searchs for strings with specific tillage intensity parameters 
    that match a given tillage operation. These are then replaced
    with new strings to match the different management scenarios
 
    parent = parent directory where files are located
    file_type = file type. Use .man for management

    This script was used to adjust tillage intensity parameters to match the
    reduced tillage system. The number of hillslopes selected depend on the
    adoption rate in the management scenario selected.
    '''

    import os
    import pandas as pd

    hillslopes = [x for x in os.listdir(parent) if x.endswith(file_type)]

    for HS_file in hillslopes:

        # if found, add file name to end of path
        current_path = ''.join((parent, HS_file))
        # read in file
        reading_file = open(current_path, "r")

        def replace_string(old_string, new_string):
            '''
            Replace old_string with new_string
            ''' 

            with open(current_path, "r") as file:

                # assign blank new file content
                new_file_content = ""

                # iterate through all lines in file
                for line in file:
                    #strip line for editing
                    stripped_line = line.strip() 
                    #replace old string with new string
                    new_line = stripped_line.replace(old_string, new_string) 
                    # add new line to new_file_content
                    new_file_content += new_line +"\n"

                #close reading file
                file.close()
                # open file for writing
                writing_file = open(current_path, "w")
                # write new content to file
                writing_file.write(new_file_content)
                #close file
                writing_file.close()

        #set up strings for tandem disk
        norm_tan_1 = '0.5000 0.5000 0'
        norm_tan_2 = '0.0500 0.2300 0.5000 0.5000 0.0260 1.0000 0.1000'

        new_tan_1 = '0.0000 0.0000 0'
        new_tan_2 = '0.0000 0.0000 0.0000 0.0000 0.0000 0.0000 0.0000'

        #set up strings for field cultivator
        norm_fc_1 = '0.6000 0.3500 0'
        norm_fc_2 = '0.0250 0.3000 0.6000 0.3500 0.0150 1.0000 0.0500'

        new_fc_1 = '0.5000 0.3500 0'
        new_fc_2 = '0.0250 0.3000 0.5000 0.3500 0.0150 1.0000 0.0500'

        kernza_fc_1 = '0.5000 0.0000 0'
        kernza_fc_2 = '0.0250 0.3000 0.5000 0.0000 0.0150 1.0000 0.0500'


        #set up strings for mid-summer cultivator
        norm_cu_1 = '0.4000 0.2000 0'
        norm_cu_2 = '0.0750 0.7500 0.4000 0.2000 0.0150 0.8500 0.0500'

        new_cu_1 = '0.0000 0.0000 0'
        new_cu_2 = '0.0000 0.0000 0.0000 0.0000 0.0000 0.0000 0.0000'


        #set up strings for Chisel plow 

        norm_chis_1 = '0.5000 0.3000 0'
        norm_chis_2 = '0.0500 0.3000 0.5000 0.3000 0.0230 1.0000 0.1500'

        new_chis_1 = '0.0000 0.0000 0'
        new_chis_2 = '0.0000 0.0000 0.0000 0.0000 0.0000 0.0000 0.0000'

        kernza_chis_1 = '0.0000 0.3000 0'
        kernza_chis_2 = '0.0500 0.3000 0.0000 0.3000 0.0230 1.0000 0.1500'



        #implement future tillage values specific to hillslopes with kernza
        if 'Kernza' in reading_file.read():

            #replace tandem values with all zeros, do not want tandem in rotation
            replace_string(norm_tan_2, new_tan_2)
            replace_string(norm_tan_1, new_tan_1)

            #replace field cultivator values with future kernza tillage values 
            replace_string(norm_fc_2, kernza_fc_2)
            replace_string(norm_fc_1, kernza_fc_1)

            #replace cultivator values with future tillage values
            replace_string(norm_cu_2, new_cu_2)
            replace_string(norm_cu_1, new_cu_1)

            #replace chisel plow values with future kernza tillage values
            replace_string(norm_chis_2, kernza_chis_2)
            replace_string(norm_chis_1, kernza_chis_1)

        #implement future tillage values to all other hillslopes
        if 'Kernza' not in reading_file.read():

            #replace tandem values with all zeros, do not want tandem in rotation
            replace_string(norm_tan_2, new_tan_2)
            replace_string(norm_tan_1, new_tan_1)

            #replace field cultivator values with future kernza tillage values 
            replace_string(norm_fc_2, new_fc_2)
            replace_string(norm_fc_1, new_fc_1)

            #replace cultivator values with future tillage values
            replace_string(norm_cu_2, new_cu_2)
            replace_string(norm_cu_1, new_cu_1)

            #replace chisel plow values with future kernza tillage values
            replace_string(norm_chis_2, new_chis_2)
            replace_string(norm_chis_1, new_chis_1)


#Example for the Stearns watershed with 100% adoption of reduced tillage
# and different perennial crop adoption rates.

#watershed list
wshed_lst = ['ST1']

#Management scenario list
scen_lst = ['Per_m20_100','Per_p20_100','Per_B_100','Per_0_100']

#climate model scenario list
mod_lst = ['B3_59', 'B3_99', 'B4_59', 'B4_99',\
           'L3_59', 'L3_99', 'L4_59', 'L4_99',\
           'Obs'] 

#Hillslope selection list (numerical portion of ID)
ST1_HS_lst = [2,4,5,6,8,9,12,13,17,19,20,23,24,25,26,29,32,37,41,45,47,\
              51,52,53,55,57,59,60,64,77,78,84,88,101,105,117,120,122,125,\
              129,146,154,166,173,178,181,185,186,194,201,214,249,286,298,\
              305,306,309,313,317,318,322,333,346,354,358,362,382]


#loop through watershed list, climate list, and then management scenario lsit
for wshed in wshed_lst:

    for mod in mod_lst:
        
        for scen in scen_lst:

            #define directory with hillslope projects
            parent_dir = 'C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/New_Runs/{}/{}/wepp/runs/'.format(wshed,mod,scen)      
            adjust_residue_CsvT(parent_dir, '.man')

#%%