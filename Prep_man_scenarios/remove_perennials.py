import os,shutil
import pandas as pd

def find_rotations(runs_dir):
    '''
    Finds all crops in each hillslope .man file. The crops are appended to a separate list
    for each hillslope which can be interpreted as a crop rotation. Specific years are 
    not known but also not necessary to know for downstream analysis
    
    Returns dataframe with two columns for IDs and rotations in string format
    '''
    
    # Create lists for appending rotations and IDs from all hillslopes
    rot_lst = []
    ID_lst = []
    OFE_lst = []
    
    # Loop through all management files in runs_dir
    for file in os.listdir(runs_dir):
        if file.endswith('.man'):
            
            #Create temporary list for appending all crops present in 
            #a management file (resets each iteration)
            temp_lst = []

            #open file for reading
            with open(str(runs_dir + file)) as f:

                #read lines 
                lines = f.readlines()

                OFE_line = lines[6]

                OFE_lst.append(OFE_line[0])

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
    rotations = pd.DataFrame({'ID':ID_lst, 'Rotation':new_rot_lst, 'OFE':OFE_lst})
    
    return rotations


#### Replace all alfalfa and pasture hillslopes with corn/soy rotation files
#### corn/soy .man replacement file must match the number of OFEs in original 
#### alfalfa/pasture file that is being replaced.

mods = ['Obs','L3_59','L3_99','L4_59','L4_99',\
        'B3_59','B3_99','B4_59','B4_99']

wshed_lst = ['DO1', 'GO1', 'ST1']

for wshed in wshed_lst:
    for mod in mods:

        runs_dir = 'C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/New_Runs/{}/CC_B/wepp/runs/'.format(wshed,mod)
        HS_info = find_rotations(runs_dir)

        #loop through columns in HS_info
        for ID, rot, OFE in zip(HS_info['ID'], HS_info['Rotation'], HS_info['OFE']):

            #select rows that have alfalfa or pasture in rotation
            if 'Alf' in rot or 'Pasture' in rot:

                #define source file directory (holds corn soy .man files for different OFE nums)
                source_dir = 'C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/New_Runs/corn_soy_files/'.format(wshed)

                #define destination directory (destination = directory of file being replaced)
                dest_dir = 'C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/New_Runs/{}/CT_100/wepp/runs/'.format(wshed,mod)

                #define path to source corn soy OFE file
                source_path = str(source_dir + 'OFE_' + OFE + '.man')

                #define destination path 
                dest_path = str(dest_dir + ID + '.man')

                #replace alfalfa/pasture file with pure corn_soy file
                shutil.copy(source_path, dest_path)

        


