from dataclasses import replace


def adjust_residue_base(parent, file_type):
    '''
    Function that scans a directory to find a specific file type 
    (.man in this case). Once the file type is located, the function
    searchs for strings with specific tillage intensity parameters 
    that match a given tillage operation. These are then replaced
    with new strings to match the different management scenarios
 
    parent = parent directory where files are located
    file_type = file type. Use .man for management

    This specific script is for adjusting management operation in all 
    baseline files. Tandem tillage operations are removed to better represent
    current tillage practices in Minnesota
    '''

    import os
    import pandas as pd

    for file_name in os.listdir(parent):

        # search for file in directory
        if file_name.endswith(file_type):

            # if found, add file name to end of path
            current_path = ''.join((parent, file_name))
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


            #implement future tillage values specific to hillslopes with kernza
            if 'Kernza' in reading_file.read():

                #replace tandem values with all zeros, do not want tandem in rotation
                replace_string(norm_tan_2, new_tan_2)
                replace_string(norm_tan_1, new_tan_1)

            #implement future tillage values to all other hillslopes
            if 'Kernza' not in reading_file.read():

                #replace tandem values with all zeros, do not want tandem in rotation
                replace_string(norm_tan_2, new_tan_2)
                replace_string(norm_tan_1, new_tan_1)


wshed_lst = ['BE1', 'DO1', 'GO1', 'RO1', 'ST1']

for wshed in wshed_lst:
    parent_dir = 'C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/Runs/Base/Obs/wepp/runs/'.format(wshed)        
    adjust_residue_base(parent_dir, '.man')