from EPyT_IWS.functions import fn
from EPyT_IWS.functions import graph
from os import getcwd
import sys
import subprocess

'''Install EpyT and import EPANET'''
subprocess.call([sys.executable, '-m', 'pip', 'install', 'epyt'])
fn().info1_display()
from epyt import epanet

'''INPUT'''
network = 'Suvarnadhara_final3'  # Network name

'''Load network'''
file_path = getcwd() + '\\Networks\\' + str(network) + '.inp'
d = epanet(file_path)

'''INPUTS'''
omitted_nodes = ['1']  # Name(s) of node(s) omitted from adding artificial (and/or) imaginary string
a_nodes = []  # Name(s) of node(s) with Type A consumer behaviour
pc_demand = 60  # Per capita demand in Litres per day
household = 5  # Average number of consumers per household
tank_in_pipe_name = ['1'] # Name(s) of the inflow pipe(s) to the tank
tank_out_pipe_name = ['P-448'] # name(s) of the outflow pipe(s) from the tank

'''Get consumer type data'''
cons_type_info = fn().consumer_type(d, d.getNodeCount(), d.getNodeReservoirCount(), d.getNodeTankCount(), a_nodes,
                                    omitted_nodes)

'''Modifying the network'''
elevation_data = fn().node_elevations(d)
base_demand_data = fn().node_base_demands(d)
demand_nodes_org = d.getNodeCount() - d.getNodeReservoirCount() - d.getNodeTankCount()  # Storing the original count
# of demand nodes in the network
for n in range(demand_nodes_org):
    '''Setting node base demand to zero'''
    set_zero_base_demand = fn().set_zero_base_demand(d, n, omitted_nodes)

    '''Adding two artificial pseudo nodes (for connecting flow control valve)'''
    artificial_pseudo_nodes_data = fn().get_artificial_pseudo_nodes_info(d, n, cons_type_info)
    add_artificial_pseudo_nodes = fn().add_artificial_pseudo_nodes(d, n, artificial_pseudo_nodes_data)

    '''Adding artificial overhead tank'''
    artificial_oht_data = fn().get_artificial_oht_info(d, n, pc_demand, household, cons_type_info, elevation_data,
                                                       base_demand_data)
    add_artificial_oht = fn().add_artificial_oht(d, n, artificial_oht_data)

    '''Adding artificial consumer node (point where original water consumption occurs)'''
    artificial_consumer_node_data = fn().get_artificial_consumer_node_info(d, n, base_demand_data[n], cons_type_info)
    add_artificial_consumer_node = fn().add_artificial_consumer_node(d, n, artificial_consumer_node_data)

    '''Adding artificial pseudo pipe between ferrule point (node) and pseudo node-1'''
    artificial_pseudo_pipe_data = fn().get_artificial_pseudo_pipe_info(d, n, cons_type_info)
    add_artificial_pseudo_pipe = fn().add_artificial_pseudo_pipe(d, n, artificial_pseudo_pipe_data)

    '''Adding artificial FCV between pseudo nodes'''
    artificial_FCV_data = fn().get_artificial_FCV_info(d, n, cons_type_info)
    add_artificial_FCV = fn().add_artificial_FCV(d, n, artificial_FCV_data)

    '''Adding artificial pipe between pseudo node-2 and overhead tank'''
    artificial_pipe_to_oht_data = fn().get_artificial_pipe_to_oht_info(d, n, pc_demand, household, base_demand_data,
                                                                       cons_type_info)
    add_artificial_pipe_to_oht = fn().add_artificial_pipe_to_oht(d, n, artificial_pipe_to_oht_data)

    '''Adding artificial pipe between artificial overhead tank and artificial consumer node'''
    artificial_pipe_to_consumer_data = fn().get_artificial_pipe_to_consumer_info(d, n, pc_demand, household,
                                                                                 base_demand_data, cons_type_info)
    add_artificial_pipe_to_consumer = fn().add_artificial_pipe_to_consumer(d, n, artificial_pipe_to_consumer_data)

'''Save modified network'''
mod_network = network + '_mod'
file_path_mod = getcwd() + '\\Networks\\' + str(mod_network) + '.inp'
d.saveInputFile(file_path_mod)

'''INPUTS'''
d.setTimeHydraulicStep(300)  # Simulation time step in seconds
d.setTimeSimulationDuration(20 * 24 * 3600)  # Simulation time duration in seconds

'''Update the simulation information'''
node_names = d.getNodeNameID()
link_names = d.getLinkNameID()
dh = d.getTimeHydraulicStep()
T = d.getTimeSimulationDuration()
total_h = int(T / dh)
d.openHydraulicAnalysis()
d.initializeHydraulicAnalysis()

'''Initializing the variables'''
t, t_step, Time, Pressure, Demand, Flow, TankVolume = 0, 0, [], [], [], [], []

'''Starting the hydraulic simulation'''
while t < T:
    for i in range(demand_nodes_org):
        if cons_type_info[i] != '' and cons_type_info[i] == 'B':
            if t_step == 0:
                p_head_node = 0
            else:
                p_head_node = Pressure[t_step - 1][i]
            artificial_FCV_index = link_names.index(node_names[i] + str('-FCV')) + 1
            artificial_FCV_setting = fn().compute_artificial_FCV_setting(d, i, p_head_node)
            d.setLinkSettings(artificial_FCV_index, artificial_FCV_setting)

    t = d.runHydraulicAnalysis()
    Time.append(t)
    Pressure.append(d.getNodePressure())
    Demand.append(d.getNodeActualDemand())
    Flow.append(d.getLinkFlows())
    TankVolume.append(d.getNodeTankVolume())
    d.nextHydraulicAnalysisStep()
    t_step += 1
    print("Hydraulic simulation time (s): %d\nHydraulic simulation time step: %d" % (t, t_step))
d.closeHydraulicAnalysis()

'''Processing the analysis report'''
filtered_steps = fn().filter_time_steps((len(Time) - 1) / (int((d.getTimeSimulationDuration() / dh) + 1) - 1),
                                        len(Time), dh, Time)
hydraulic_report = fn().final_report(d, filtered_steps, Time, Pressure, Demand, Flow, TankVolume)

dp = d.getTimePatternStep()
total_p = int(T/ dp)
'''Generating the output array for pipe flows'''
Flow_out = fn().make_Flow_output(d, dh, dp, total_p, hydraulic_report[3])
'''Generating the output array for tank volumes'''
TankVolume_out = fn().make_TankVolume_output(d, dh, dp, total_p, hydraulic_report[4])
'''Generating the output array for required demands at every node'''
Required_Demand_out = fn().make_Required_Demand_output(d, demand_nodes_org, total_p, cons_type_info)
'''Determing demand deficit values at every pattern step for every node
--- If the water volume avaialble in the household tank available during a pattern step is 
more than the required demand, then deficit is zero. Else, deficit is estimated as:
    ((volume available - volume required)/ volume required) * 100
For omitted nodes, deficit is -100 ---
'''
Demand_deficit_out = fn().compute_demand_deficit(d, demand_nodes_org, dp, total_p, TankVolume_out,
                                                 Required_Demand_out, cons_type_info)

'''Determing relative distribution of water values at every pattern step for every node
--- ratio of water withdrawn at any node to the water delivered
For omitted nodes, value is -100---
'''
Relative_distribution_out = fn().compute_relative_distribution(d, demand_nodes_org, tank_out_pipe_name, Flow_out, 
                                                               cons_type_info)   
folder_name = getcwd() + '\\Analysis_Results'

'''Creating CSV files'''
csv_out = fn().make_csv_out(Flow_out, TankVolume_out, Demand_deficit_out, Relative_distribution_out, folder_name)

'''Creating plots'''
plot_strored_volume_vs_time = graph().plot_stored_volume_vs_time(d, demand_nodes_org, TankVolume_out, cons_type_info, 
                                                                 folder_name)
plot_required_volume_vs_time = graph().plot_required_volume_vs_time(d, demand_nodes_org, dp, Required_Demand_out, 
                                                                    cons_type_info, folder_name)
plot_volume_surplus_deficit_vs_time = graph().plot_volume_surplus_deficit_vs_time(d, demand_nodes_org, dp, TankVolume_out, 
                                                                                  Required_Demand_out, cons_type_info, 
                                                                                  folder_name)
plot_deficit_vs_time = graph().plot_deficit_percent_vs_time(d, demand_nodes_org, Demand_deficit_out, cons_type_info, 
                                                            folder_name)
plot_relative_distribution_vs_time = graph().plot_relative_distribution_vs_time(d, demand_nodes_org, Relative_distribution_out, 
                                                                                cons_type_info, folder_name)

"""CHECKING THE MASS BALANCE"""
check = fn().check_mass_balance(d, demand_nodes_org, tank_in_pipe_name, tank_out_pipe_name, Flow_out, cons_type_info)

d.unload()
print("\nAnalysis completed.")