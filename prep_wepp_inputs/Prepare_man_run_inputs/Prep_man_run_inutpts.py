def prep_input_files(base_files, HUC12_ID, HUC12_xl_out):
    '''
    This function performs the following tasks:

    1.) HUC12 IDs are removed from file names and replaced with the letter p
    2.) WEPP run files are created
    3.) Crop rotations, average slopes, and soil types for each hillslope are extracted
    4.) Rotations in .man files are extended to 60 years so that WEPP can run the max
        number of years in each climate file (WEPP stops after the final year in a climate
        file is reached)


    base_files = directory holding the raw soil, topography, and management 
    input files from the DEP

    HUC12_ID = ID number of HUC12 watershed from DEP

    HUC12_xl_out = name of watershed that will be inserted into the name of 
    an output file that contains information on hillslope rotation, slopes, and
    soil types

    '''
    
    import os
    import pandas as pd
    import re
    from statistics import mean
    
    print('Renaming files to WEPP format...')
    
    #Rename all file types in base_files
    for file in os.listdir(base_files):
        if file.startswith(HUC12_ID):
            file_num = file.replace(HUC12_ID, '')
            old = str(base_files + file)
            new = str(base_files + 'p' + file_num)

            os.rename(old, new)



    def create_run_file(hill, p_hill, run_yrs):
        '''
        Creates .run files necessary for running hillslopes in WEPP model
        
        hill = hillslope ID for output files
        p_hill = hillslope ID for input files
        run_yrs = number of years to run WEPP
        '''
        
        run_lst = []
        
        def create_run_inputs(input_lst):
            '''
            Creates a list of inputs for the WEPP model application

            input_lst will be written to a file in .run format
            '''
            input_lst = ['m','Yes','1','1','No','2','No',\
                '../output/{}.loss.dat'.format(hill), 'No',\
                'Yes','../output/{}.plant.dat'.format(hill),\
                'Yes','../output/{}.soil.dat'.format(hill), 'No', 'No',\
                'Yes', '../output/{}.ebe.dat'.format(hill),\
                'Yes', '../output/{}.element.dat'.format(hill),'No', 'No',\
                'Yes', '../output/{}.yield.dat'.format(hill),\
                '{}.man'.format(p_hill), '{}.slp'.format(p_hill),\
                '{}.cli'.format(p_hill), '{}.sol'.format(p_hill),\
                '0', run_yrs, '0']

            return input_lst
        
        inputs = create_run_inputs(run_lst)
        
        #write list of input commands to a blank .run file
        with open(str(base_files + '{}.run'.format(p_hill)), 'w+') as file:
            for line in inputs:
                file.writelines(str(line)+'\n')
    
    print('Creating .run files...')
    
    #loop through hillslopes in base_files
    for file in os.listdir(base_files):
        #only select one file type to get hill_ids so that multiple run files
        #are not created
        if file.endswith('.man'):
            
            #create names of files being specified in the .run file
            #(i.e. p1.man, H1.man, etc)
            input_file_name = str('p' + str(file[1:-4]))
            output_file_name = str('H' + str(file[1:-4]))
            
            #run create_run_file for each hillslope in base_files
            create_run_file(output_file_name, input_file_name, 60)
            
            
            
    def find_rotations():
        '''
        Finds all crops in each hillslope .man file. The crops are appended to a separate list
        for each hillslope which is can be interpreted as a crop rotation. Specific years are 
        not known but also not necessary to know for downstream analysis
        
        Returns dataframe with two columns for IDs and rotations in string format
        '''
        
        # Create lists for appending rotations and IDs from all hillslopes
        rot_lst = []
        ID_lst = []
        
        # Loop through all management files in base_files
        for file in os.listdir(base_files):
            if file.endswith('.man'):
                
                #Create temporary list for appending all crops present in 
                #a management file (resets each iteration)
                temp_lst = []

                #open file for reading
                with open(str(base_files + file)) as f:

                    #read lines 
                    lines = f.readlines()

                    #loop through lines
                    for line in lines:
                        #append crops to temp_lst by name

                        if line.startswith('Corn'):
                            temp_lst.append('Corn')

                        if line.startswith('Cor_0967'):
                            temp_lst.append('Corn_2')

                        if line.startswith('ALFALFA'):
                            temp_lst.append('Alf')

                        if line.startswith('Soy_2194'):
                            temp_lst.append('Soy')

                        if line.startswith('`Bromegrass-High'):
                            temp_lst.append('Pasture')

                        if line.startswith('Wheat'):
                            temp_lst.append('Wheat')

                #append temp_lst to rot_lst...each file has separate rotation
                rot_lst.append(temp_lst)
                
                #Append IDs to a list 
                ID_lst.append(file[:-4])

        #remove corn duplicates, two different types of corn in .man files, but 
        #only one is necessary for downstream analysis
        for lst in rot_lst:
            if 'Corn' in lst and 'Corn_2' in lst:
                lst.remove('Corn_2')

        #create new list that combines all crops in a list to a single string
        #separated by a '_'
        new_rot_lst = []
        for rot in rot_lst:
            comb_rot = '_'.join(rot)
            new_rot_lst.append(comb_rot)
            

        #create dataframe of hillslope IDs and the respective rotations
        rotations = pd.DataFrame({'ID':ID_lst, 'Rotation':new_rot_lst})
        
        return rotations
    
    print('Finding crop rotations...')
    
    # Create dataframe for hillslope information
    hillslope_info = find_rotations()
    
    
    def find_slopes():
        '''
        Calculates average slope values for each hillslopes and returns a list
        of the calculated values
        '''
        
        avg_slopes = []

        for file in os.listdir(base_files):
            #loop through slope/topography files in base_files
            if file.endswith('.slp'):  
                #join path and file
                current_path = ''.join((base_files, "/", file))
                
                # read in file
                reading_file = open(current_path, "r")

                lines = reading_file.readlines() 

                #skip first 8 lines - they do not include any relevant data
                core_slope_lines = lines[8::]
                
                #get lines with slope data
                slope_lines = core_slope_lines[0::2]
                
                #get individual data line with slope points
                slope_line = str(''.join(slope_lines))

                #Split line with slope points into individual list items
                split_vals = re.split('\s|[,]', slope_line)

                #Remove blank list items from .split()
                slope_points = [x for x in split_vals if x.strip()]

                #Select the slope values from each point
                slope_vals = slope_points[1::2]

                #change to float values
                slope_vals = [float(i) for i in slope_vals] 

                #get average slope values of hillslope and append to list
                avg_slope = round(mean(slope_vals), 4)
                avg_slopes.append(avg_slope)

        return avg_slopes
    
    print('Finding average slope values...')
    
    avg_slopes = find_slopes()
    
    #Assign avg_slopes to hillslope_info df
    hillslope_info['avg_slopes'] = avg_slopes
    
    
    
    def find_soil_types():
        '''
        Calculates average %sand and %clay content for each hillslope and 
        appends them to separate lists which are returned 
        '''
        sand_vals = []
        clay_vals = []

        for file in os.listdir(base_files):
            if file.endswith('.sol'):  # search for file in directory
                current_path = ''.join((base_files, "/", file)) # if found, add file name to end of path
                reading_file = open(current_path, "r") # read in file

                lines = reading_file.readlines()  #read lines to a list

                core_soil_lines = lines[4::]  #skip first 4 lines

                data_lines = []

                for line in core_soil_lines:
                    sub_line_1 = '0 0.000000 0\n'
                    sub_line_2 = '0.750000'
                    if sub_line_1 in line:
                        pass
                    elif sub_line_2 in line:
                        pass
                    else:
                        data_lines.append(str(line))

                soil_vals = []

                for line in data_lines:
                    soil_vals.append(line.strip())

                soil_df = pd.DataFrame({'line': soil_vals})

                soil_df[['Depth', '%sand', '%clay', '%OM', 'CEC', '%rock']] = soil_df['line'].str.split(" ", expand=True)

                soil_df.drop(columns = 'line', inplace = True)

                soil_df

                sand = soil_df['%sand'].astype(float).mean()
                clay = soil_df['%clay'].astype(float).mean()

                sand_vals.append(sand)
                clay_vals.append(clay)
                
        return sand_vals, clay_vals
    
    print('Finding soil types...')
    sand_vals, clay_vals = find_soil_types()
    
    hillslope_info['sand%'] = sand_vals
    hillslope_info['clay%'] = clay_vals
    
    print(hillslope_info)
    
    
    def Increase_rot_length():
        '''
        Increases the rotation length in the management section by copying the
        rotation and then repeating it 4 times for a total of 60 years

        Only needed if the management section of the .man files have rotation lengths
        less than the number of years in the climate .cli file.
        '''
        for file in os.listdir(base_files):
            #select all .man files in the directory
            if file.endswith('.man'):
                current_path = ''.join((base_files, "/", file))
            
                # read in file
                with open(current_path, "r+") as file:
                    #read in all lines to list
                    lines = file.readlines()
                
                    if '# Rotation 1: year 1 to 15\n' in lines:
                        #Find line that is the same in all files and use it as a reference point
                        start_line = lines.index('# Rotation 1: year 1 to 15\n')
                    if '# Rotation 1: year 1 to 8\n' in lines:
                        start_line = lines.index('# Rotation 1: year 1 to 8\n')

                    #Set full rotation to new list of lines and repeat it four times
                    full_rot_lines = lines[(int(start_line)+3)::]

                    # move file pointer to the beginning of the file
                    file.seek(0)
                    # truncate the file
                    file.truncate()
                    #Write exisiting and new lines to file
                    file.writelines(lines[0:int(start_line)]) #Exisiting

                    def add_single_rotation():
                        '''
                        writes a full crop rotation to the bottom of the file
                        '''
                        for line in full_rot_lines:
                            file.writelines(line)
                        file.writelines('\n')

                    #Add 4 rotations for 60 years total
                    add_single_rotation()
                    add_single_rotation()
                    add_single_rotation()
                    add_single_rotation()

                    file.close()
                
                # Replace 15 total years with 60

                def replace_string(old_string, new_string):
                    '''
                    replaces string in file with a new string
                    '''
                    reading_file = open(current_path, "r")
                    # assign blank content
                    new_file_content = ""

                    #iterate through all lines in .man file
                    for line in reading_file:
                        stripped_line = line.strip() 
                        new_line = stripped_line.replace(old_string, new_string) 
                        new_file_content += new_line +"\n" # add new line to new_file_content
                    reading_file.close()

                    writing_file = open(current_path, "w") # open file for writing
                    writing_file.write(new_file_content) # write new content to file
                    writing_file.close()

                replace_string('15 # (total) years in simulation', '60 # (total) years in simulation')
                replace_string('15  # years in rotation', '60  # years in rotation')
                replace_string('8  # years in rotation', '60  # years in rotation')          
    
    print('Increasing crop rotation length in files...')
    Increase_rot_length()

    #Send hillslope_info to excel spreadsheet
    hillslope_info.to_excel('C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/{}_info.xlsx'.format(HUC12_xl_out, HUC12_xl_out))



##### After these edits were complete, the WEPP files were copied into directories for each
##### climate and management scenario combination in every watershed. The fully prepared cligen files 
##### were then copied into their corresponding directories.