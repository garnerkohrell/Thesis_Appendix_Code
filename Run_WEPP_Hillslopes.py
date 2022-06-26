def run_wepp(wepppy_win_dir, mod_dir, scen_lst):
    '''
    Runs wepp using the run_project.py script in rogderlew's wepppy 
    repository. This allows all hillslopes within each scenario directory
    to be run without need of the WEPP GUI.
    '''

    import os

    #change directory to wepppy_win_dir
    os.chdir(wepppy_win_dir)

    #Run for all management scenarios in a given climate model directory
    for scen in scen_lst:
        cli_scen_dir = str(mod_dir + scen)
        os.system('python3 run_project.py {}'.format(cli_scen_dir))


#define path to directory with wepppy windows bootstrap scripts
wepppy_win_dir = 'C:/Users/Garner/Soil_Erosion_Project/wepppy-win-bootstrap-master/scripts'

### Example for Stearns watershed
wshed_lst = ['ST1']

#Run for all adoption rates in the perennial scenarios
scen_lst = ['Per_0', 'Per_m20', 'Per_B', 'Per_p20']

#Run for all climate models
mod_lst = ['Obs','L3_59','L3_99','L4_59','L4_99',\
           'B3_59','B3_99','B4_59','B4_99']

#loop through watersheds in wshed_lst
for wshed in wshed_lst:
    #loop through climate models in mod_lst
    for mod in mod_lst:

        #define directory for specific watershed and climate model
        mod_dir = str('C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/New_Runs/{}/'.format(wshed,mod))
        
        #run function defined above for all management scenarios in scen_lst
        run_wepp(wepppy_win_dir, mod_dir, scen_lst)