#%%

def adjust_residue_CC(parent, file_type):
    '''
    Function that scans a directory to find a specific file type 
    (.man in this case). Once the file type is located, the function
    searchs for strings with specific tillage intensity parameters 
    that match a given tillage operation. These are then replaced
    with new strings to match the different management scenarios
 
    parent = parent directory where files are located
    file_type = file type. Use .man for management

    This specific script is for adjusting management operation in the
    cover crop files
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


        #set up strings for Chisel plow 

        norm_chis_1 = '0.5000 0.3000 0'
        norm_chis_2 = '0.0500 0.3000 0.5000 0.3000 0.0230 1.0000 0.1500'

        new_chis_1 = '0.0000 0.0000 0'
        new_chis_2 = '0.0000 0.0000 0.0000 0.0000 0.0000 0.0000 0.0000'

        #set up strings for tandem disk
        norm_tan_1 = '0.5000 0.5000 0'
        norm_tan_2 = '0.0500 0.2300 0.5000 0.5000 0.0260 1.0000 0.1000'

        new_tan_1 = '0.0000 0.0000 0'
        new_tan_2 = '0.0000 0.0000 0.0000 0.0000 0.0000 0.0000 0.0000'



        #implement future tillage values specific to hillslopes with kernza
        if 'Ryegrass cover crop' in reading_file.read():

            #replace chisel plow values with future kernza tillage values
            replace_string(norm_chis_2, new_chis_2)
            replace_string(norm_chis_1, new_chis_1)

            #replace tandem values with all zeros, do not want tandem in rotation
            replace_string(norm_tan_2, new_tan_2)
            replace_string(norm_tan_1, new_tan_1)

        else:
            #replace tandem values with all zeros, do not want tandem in rotation
            replace_string(norm_tan_2, new_tan_2)
            replace_string(norm_tan_1, new_tan_1)


#Example for the Stearns watershed

wshed_lst = ['ST1']

mod_lst = ['B3_59', 'B3_99', 'B4_59', 'B4_99',\
           'L3_59', 'L3_99', 'L4_59', 'L4_99',\
           'Obs']


for wshed in wshed_lst:
    for mod in mod_lst:

        parent_dir = 'C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/New_Runs/{}/Per_B/wepp/runs/'.format(wshed,mod)        
        adjust_residue_CC(parent_dir, '.man')

#%%