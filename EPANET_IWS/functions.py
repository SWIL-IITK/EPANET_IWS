import numpy as np
import math
import copy
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib as mpl
import os


class fn:

    def info1_display(self):
        print("EPyT installed successfully.")

    def consumer_type(self, d, num1, num2, num3, arr1, arr2):
        """Defining the consumer types at nodes
        :d: EPANET model
        :num1: count of nodes
        :num2: count of reservoirs
        :num3: count of tanks
        :arr1: names of type A nodes
        :arr2: names of omitted nodes
        :return: list of consumer types at every node (except omitted one(s))
        """
        consumer_type = []
        node_names = d.getNodeNameID()
        for n in range(num1 - num2 - num3):
            name = node_names[n]
            if name not in arr2:
                if name in arr1:
                    consumer_type.append('A')
                else:
                    consumer_type.append('B')
            else:
                consumer_type.append('')
        print("Consumer type data updated successfully.")
        return consumer_type

    def node_elevations(self, d):
        """Getting the elevations of nodes
        :d: EPANET model
        :return: list of node elevations in m
        """
        node_elevations = d.getNodeElevations()
        flow_unit = d.getFlowUnits()
        if flow_unit == 'GPM':
            node_elevations = np.multiply(node_elevations, 0.3048)
        print("Node elevations updated.")
        return node_elevations

    def node_base_demands(self, d):
        """Getting the base demands of nodes
        :d: EPANET model
        :return: array of node base demands in cu.m/s
        """
        base_demand_dict = d.getNodeBaseDemands()
        base_demand_array = list(base_demand_dict.items())
        node_base_demands = base_demand_array[0][1]
        flow_unit = d.getFlowUnits()
        if flow_unit == 'GPM':
            node_base_demands = np.multiply(node_base_demands, 6.3e-5)
        elif flow_unit == 'LPS':
            node_base_demands = np.multiply(node_base_demands, 1e-3)
        elif flow_unit == 'LPM':
            node_base_demands = np.multiply(node_base_demands, 1.67e-5)
        elif flow_unit == 'CMH':
            node_base_demands = np.multiply(node_base_demands, (1 / 3600))
        print("Node base demands updated.")
        return node_base_demands

    def set_zero_base_demand(self, d, num1, arr1):
        """Setting zero base demands at nodes (except omitted ones)
        :d: EPANET model
        :num1: node index
        :arr1: names of omitted nodes
        :return: set base demand to zero
        """
        node_names = d.getNodeNameID()
        if node_names[num1] not in arr1:
            d.setNodeBaseDemands(num1 + 1, 0)

    def get_artificial_pseudo_nodes_info(self, d, num1, arr1):
        """Generating pseudo node properties at every node
        :d: EPANET model
        :num1: node index
        :arr1: consumer type list
        :return: list of pseudo nodes properties
        """
        # TODO
        node_names = d.getNodeNameID()
        if arr1[num1] != '' and arr1[num1] == 'B':
            elevation_difference = 0  # 0 m difference between ferrule point and the pseudo nodes
            demand_pseudo_node = 0  # zero base demand
            elevation_pseudo_node = d.getNodeElevations()[num1] + elevation_difference
            pseudo_node_properties = [elevation_pseudo_node, demand_pseudo_node]
            print("Artificial pseudo node properties generated for Node '" + node_names[num1] + "'")
        else:
            pseudo_node_properties = []
            print("Omitted Node '" + node_names[num1] + "'. No information generated for artificial pseudo node.")
        return pseudo_node_properties

    def add_artificial_pseudo_nodes(self, d, num1, arr1):
        """Adding artificial pseudo nodes at every node
        :d: EPANET model
        :num1: node index
        :arr1: pseudo node properties
        :return: add two artificial pseudo nodes
        """
        node_names = d.getNodeNameID()
        if arr1 != []:
            for i in range(2):
                artificial_pseudo_node_name = node_names[num1] + str('-PseudoN-') + str(i + 1)
                artificial_pseudo_node_index = d.addNodeJunction(artificial_pseudo_node_name)
                d.setNodeElevations(artificial_pseudo_node_index, arr1[0])
                d.setNodeBaseDemands(artificial_pseudo_node_index, arr1[1])
            print("Artificial pseudo nodes added for Node '" + node_names[num1] + "'")

    def get_artificial_oht_info(self, d, num1, num2, num3, arr1, arr2, arr3):
        """Generating artificial overhead tank properties at every node (Type A and B)
        :d: EPANET model
        :num1: node index
        :num2: per capita demand
        :num3: number of consumers per household
        :arr1: consumer type list
        :arr2: node elevations
        :arr3: node base demands
        :return: list of artificial overhead tank properties
        """
        # TODO
        node_names = d.getNodeNameID()
        flow_unit = d.getFlowUnits()
        elevation_difference = 7  # 7 m difference between ferrule point and OHT base
        if flow_unit == 'GPM':
            elevation_difference = elevation_difference / 0.3048
        volume_oht_house = 1  # 1 cub.m (1000 L) capacity considered for individual household overhead tanks
        max_level_artificial_oht = 2  # 2 m maximum height considered for individual household overhead tanks
        initial_level_artificial_oht = 0  # Initial condition: Individual household overhead tanks are empty
        min_level_artificial_oht = 0  # 0 m is the minimum level considered
        if arr1[num1] != '' and arr1[num1] == 'B':
            elevation_artificial_oht = d.getNodeElevations()[num1] + elevation_difference
            volume_artificial_oht = volume_oht_house * math.ceil((arr3[num1] * (24 * 3600 * 1000) / num2) / num3)
            diameter_artificial_oht = math.sqrt((4 * volume_artificial_oht) / (math.pi * max_level_artificial_oht))
            if flow_unit == 'GPM':
                max_level_artificial_oht /= 0.3048
                initial_level_artificial_oht /= 0.3048
                diameter_artificial_oht *= 39.37
            artificial_oht_properties = [elevation_artificial_oht, diameter_artificial_oht, max_level_artificial_oht,
                                         min_level_artificial_oht, initial_level_artificial_oht]
            print("Artificial overhead tank properties generated for Node '" + node_names[num1] + "'")
        else:
            artificial_oht_properties = []
            print("Omitted Node '" + node_names[num1] + "'. No information generated for artificial tank.")
        return artificial_oht_properties

    def add_artificial_oht(self, d, num1, arr1):
        """Adding artificial overhead tanks at every node
        :d: EPANET model
        :num1: node index
        :arr1: artificial overhead tank properties
        :return: add a new artificial tank
        """
        node_names = d.getNodeNameID()
        if arr1 != []:
            artificial_oht_name = node_names[num1] + str('-OHT')
            artificial_oht_index = d.addNodeTank(artificial_oht_name)
            d.setNodeElevations(artificial_oht_index, arr1[0])
            d.setNodeTankDiameter(artificial_oht_index, arr1[1])
            d.setNodeTankMaximumWaterLevel(artificial_oht_index, arr1[2])
            d.setNodeTankMinimumWaterLevel(artificial_oht_index, arr1[3])
            d.setNodeTankInitialLevel(artificial_oht_index, arr1[4])
            print("Artificial overhead tank added for Node '" + node_names[num1] + "'")

    def get_artificial_consumer_node_info(self, d, num1, num2, arr1):
        """Generating 'consumer' node properties at every node (Type A and B)
        :d: EPANET model
        :num1: node index
        :num2: base demand value (cu.m/s)
        :arr1: consumer type list
        :return: list of consumer node properties
        """
        # TODO
        node_names = d.getNodeNameID()
        flow_unit = d.getFlowUnits()
        if arr1[num1] != '' and arr1[num1] == 'B':
            elevation_difference = 7  # 3 m difference between ferrule point and the actual consumer node
            if flow_unit == 'GPM':
                elevation_difference = elevation_difference / 0.304
                demand_consumer_node = num2 * (1 / 6.3e-5)
            elif flow_unit == 'LPS':
                demand_consumer_node = num2 * 1000
            elif flow_unit == 'LPM':
                demand_consumer_node = num2 * (1 / 1.67e-5)
            elif flow_unit == 'CMH':
                demand_consumer_node = num2 * 3600
            else:
                demand_consumer_node = num2
            elevation_consumer_node = d.getNodeElevations()[num1] + elevation_difference
            consumer_node_properties = [elevation_consumer_node, demand_consumer_node]
            print("Artificial consumer node properties generated for Node '" + node_names[num1] + "'")
        else:
            consumer_node_properties = []
            print("Omitted Node '" + node_names[num1] + "'. No information generated for artificial consumer node.")
        return consumer_node_properties

    def add_artificial_consumer_node(self, d, num1, arr1):
        """Adding artificial 'consumer' nodes at every node
        :d: EPANET model
        :num1: node index
        :arr1: consumer node properties
        :return: add a artificial consumer node
        """
        node_names = d.getNodeNameID()
        if arr1 != []:
            artificial_consumer_node_name = node_names[num1] + str('-CN')
            artificial_consumer_node_index = d.addNodeJunction(artificial_consumer_node_name)
            d.setNodeElevations(artificial_consumer_node_index, arr1[0])
            d.setNodeBaseDemands(artificial_consumer_node_index, arr1[1])
            d.setNodeDemandPatternIndex(artificial_consumer_node_index, 1, d.getNodeDemandPatternIndex()[1][num1])
            print("Artificial consumer node added for Node '" + node_names[num1] + "'")

    def get_artificial_pseudo_pipe_info(self, d, num1, arr1):
        """Generating artificial pseudo pipe (between ferrule point and pseudo node-1) properties
        :d: EPANET model
        :num1: node index
        :arr1: consumer type list
        :return: list of artificial pseudo pipe (between ferrule point and pseudo node-1) properties
        """
        node_names = d.getNodeNameID()
        flow_unit = d.getFlowUnits()
        artificial_pseudo_pipe_length = 0.1  # 0.1 m long pseudo pipe
        artificial_pseudo_pipe_diameter = 1000  # 1000 mm diameter
        artificial_pseudo_pipe_CHW = 130
        artificial_pseudo_pipe_rough_coeff = 0.02
        if arr1[num1] != '' and arr1[num1] == 'B':
            if flow_unit == 'GPM':
                artificial_pseudo_pipe_length /= 0.3048
                artificial_pseudo_pipe_diameter *= 0.0394
            artificial_pseudo_pipe_properties = [artificial_pseudo_pipe_length, artificial_pseudo_pipe_diameter,
                                                 artificial_pseudo_pipe_CHW, artificial_pseudo_pipe_rough_coeff]
            print("Artificial pseudo pipe (between ferrule point and pseudo node-1) properties generated for Node '" +
                  node_names[num1] + "'")
        else:
            artificial_pseudo_pipe_properties = []
            print("Omitted Node '" + node_names[
                num1] + "'. No information generated for artificial pseudo pipe (between ferrule point and "
                        "pseudo node-1).")
        return artificial_pseudo_pipe_properties

    def add_artificial_pseudo_pipe(self, d, num1, arr1):
        """Adding artificial pseudo pipe (between ferrule point and pseudo node-1)
        :d: EPANET model
        :num1: node index
        :arr1: Artificial pseudo pipe (between ferrule point and pseudo node-1) properties
        :return: add an artificial pseudo pipe between ferrule point and pseudo node-1
        """
        node_names = d.getNodeNameID()
        if arr1 != []:
            artificial_pseudo_pipe_name = node_names[num1] + str('-PseudoP')
            artificial_pseudo_pipe_index = d.addLinkPipeCV(artificial_pseudo_pipe_name, node_names[num1],
                                                           node_names[num1] + str('-PseudoN-1'))
            d.setLinkLength(artificial_pseudo_pipe_index, arr1[0])
            d.setLinkDiameter(artificial_pseudo_pipe_index, arr1[1])
            d.setLinkRoughnessCoeff(artificial_pseudo_pipe_index, arr1[2])
            d.setLinkMinorLossCoeff(artificial_pseudo_pipe_index, arr1[3])
            print("Artificial pseudo pipe (between ferrule point and pseudo node-1) added for Node '" + node_names[
                num1] + "'")

    def get_artificial_FCV_info(self, d, num1, arr1):
        """Getting artificial FCV (between pseudo nodes) properties
        :d: EPANET model
        :num1: node index
        :arr1: consumer type list
        :return: list of artificial FCV (between pseudo nodes) properties
        """
        node_names = d.getNodeNameID()
        flow_unit = d.getFlowUnits()
        artificial_FCV_diameter = 1000  # 1000 mm diameter
        if arr1[num1] != '' and arr1[num1] == 'B':
            if flow_unit == 'GPM':
                artificial_FCV_diameter *= 0.0394
            artificial_FCV_properties = [artificial_FCV_diameter]
            print("Artificial FCV (between pseudo nodes) properties generated for Node '" +
                  node_names[num1] + "'")
        else:
            artificial_FCV_properties = []
            print("Omitted Node '" + node_names[
                num1] + "'. No information generated for artificial FCV (between pseudo nodes).")
        return artificial_FCV_properties

    def add_artificial_FCV(self, d, num1, arr1):
        """Adding artificial pseudo FCV (between pseudo nodes)
        :d: EPANET model
        :num1: node index
        :arr1: Artificial FCV (between pseudo nodes) properties
        :return: add an artificial pseudo FCV between pseudo nodes
        """
        node_names = d.getNodeNameID()
        if arr1 != []:
            artificial_FCV_name = node_names[num1] + str('-FCV')
            artificial_FCV_index = d.addLinkValveFCV(artificial_FCV_name, node_names[num1] + str('-PseudoN-1'),
                                                     node_names[num1] + str('-PseudoN-2'))
            d.setLinkDiameter(artificial_FCV_index, arr1[0])
            print("Artificial FCV (between pseudo nodes) added for Node '" + node_names[num1] + "'")

    def get_artificial_pipe_to_oht_info(self, d, num1, num2, num3, arr1, arr2):
        """Generating artificial pipe (between pseudo node-2 and oht) properties
        :d: EPANET model
        :num1: node index
        :num2: per capita demand
        :num3: number of consumers per household
        :arr1: node base demands
        :arr2: consumer type list
        :return: list of artificial pipe (between pseudo node-2 and oht) properties
        """
        node_names = d.getNodeNameID()
        flow_unit = d.getFlowUnits()
        artificial_pipe_length = 10  # 10 m is the distance between ferrule point and oht inlet
        house_connection_pipe_diameter = 19.03  # in mms (0.75 in pipe)
        artificial_pipe_diameter = house_connection_pipe_diameter * (
            math.ceil((arr1[num1] * (24 * 3600 * 1000) / num2) / num3)) ** 0.38
        artificial_pipe_CHW = 130
        artificial_pipe_rough_coeff = 0.02
        if arr2[num1] != '' and arr2[num1] == 'B':
            if flow_unit == 'GPM':
                artificial_pipe_length /= 0.3048
                artificial_pipe_diameter *= 0.0394
            artificial_pipe_to_oht_properties = [artificial_pipe_length, artificial_pipe_diameter,
                                                 artificial_pipe_CHW, artificial_pipe_rough_coeff]
            print("Artificial pipe (between pseudo node-2 and overhead tank) properties generated for Node '" +
                  node_names[num1] + "'")
        else:
            artificial_pipe_to_oht_properties = []
            print("Omitted Node '" + node_names[
                num1] + "'. No information generated for artificial pipe (between pseudo node-2 and overhead tank).")
        return artificial_pipe_to_oht_properties

    def add_artificial_pipe_to_oht(self, d, num1, arr1):
        """Adding artificial pipe (between pseudo node-2 and oht)
        :d: EPANET model
        :num1: node index
        :arr1: Artificial pipe (between ferrule point and oht) properties
        :return: add an artificial pipe (between pseudo node-2 and oht)
        """
        node_names = d.getNodeNameID()
        if arr1 != []:
            artificial_pipe_to_oht_name = node_names[num1] + str('-AP_to_OHT')
            artificial_pipe_to_oht_index = d.addLinkPipeCV(artificial_pipe_to_oht_name,
                                                         node_names[num1] + str('-PseudoN-2'),
                                                         node_names[num1] + str('-OHT'))
            d.setLinkLength(artificial_pipe_to_oht_index, arr1[0])
            d.setLinkDiameter(artificial_pipe_to_oht_index, arr1[1])
            d.setLinkRoughnessCoeff(artificial_pipe_to_oht_index, arr1[2])
            d.setLinkMinorLossCoeff(artificial_pipe_to_oht_index, arr1[3])
            print("Artificial pipe (between pseudo node-2 and overhead tank) added for Node '" + node_names[num1] + "'")

    def get_artificial_pipe_to_consumer_info(self, d, num1, num2, num3, arr1, arr2):
        """Generating artificial pipe (between oht and consumer node) properties
        :d: EPANET model
        :num1: node index
        :num2: per capita demand
        :num3: number of consumers per household
        :arr1: node base demands
        :arr2: consumer type list
        :return: list of artificial pipe (between oht and consumer node) properties
        """
        node_names = d.getNodeNameID()
        flow_unit = d.getFlowUnits()
        artificial_pipe_length = 5  # 5 m is the distance between oht outlet and consumer taps
        house_supply_pipe_diameter = 12.69  # in mms (0.50 in pipe)
        artificial_pipe_diameter = house_supply_pipe_diameter * (
            math.ceil((arr1[num1] * (24 * 3600 * 1000) / num2) / num3)) ** 0.38
        artificial_pipe_CHW = 130
        artificial_pipe_rough_coeff = 0.02
        if arr2[num1] != '' and arr2[num1] == 'B':
            if flow_unit == 'GPM':
                artificial_pipe_length /= 0.3048
                artificial_pipe_diameter *= 0.0394
            artificial_pipe_to_consumer_properties = [artificial_pipe_length, artificial_pipe_diameter,
                                                      artificial_pipe_CHW, artificial_pipe_rough_coeff]
            print(
                "Artificial pipe (between overhead tank and artificial consumer node) properties generated for Node '" +
                node_names[num1] + "'")
        else:
            artificial_pipe_to_consumer_properties = []
            print("Omitted Node '" + node_names[
                num1] + "'. No information generated for artificial pipe (between overhead tank and artificial "
                        "consumer node).")
        return artificial_pipe_to_consumer_properties

    def add_artificial_pipe_to_consumer(self, d, num1, arr1):
        """Adding artificial pipe (between oht and consumer node)
        :d: EPANET model
        :num1: node index
        :arr1: Artificial pipe (between oht and consumer node) properties
        :return: add an artificial pipe (between oht and consumer node)
        """
        node_names = d.getNodeNameID()
        if arr1 != []:
            artificial_pipe_to_consumer_name = node_names[num1] + str('-AP_to_CN')
            artificial_pipe_to_consumer_index = d.addLinkPipe(artificial_pipe_to_consumer_name,
                                                              node_names[num1] + str('-OHT'),
                                                              node_names[num1] + str('-CN'))
            d.setLinkLength(artificial_pipe_to_consumer_index, arr1[0])
            d.setLinkDiameter(artificial_pipe_to_consumer_index, arr1[1])
            d.setLinkRoughnessCoeff(artificial_pipe_to_consumer_index, arr1[2])
            d.setLinkMinorLossCoeff(artificial_pipe_to_consumer_index, arr1[3])
            print("Artificial pipe (between overhead tank and artificial consumer node) added for Node '" + node_names[
                num1] + "'")

    def compute_artificial_FCV_setting(self, d, num1, num2):
        """Compute the flow setting of the artificial FCV connected to every consumer node
        :d: EPANET model
        :num1: demand node index
        :num2: node pressure head value
        """
        elevation_difference = 7  # 7 m difference between ferrule point and OHT base
        flow_unit = d.getFlowUnits()
        artificial_pipe_to_oht_index = d.getLinkNameID().index(d.getNodeNameID()[num1] + str('-AP_to_OHT')) + 1

        L = int(d.getLinkLength(artificial_pipe_to_oht_index))  # length of artificial pipe to OHT
        D = int(d.getLinkDiameter(artificial_pipe_to_oht_index))  # diameter of artificial pipe to OHT
        if flow_unit == 'GPM':
            L *= 0.3048
            D /= 0.0394
            num2 *= 0.70325
        CHW = int(d.getLinkRoughnessCoeff(artificial_pipe_to_oht_index))  # CHW of artificial pipe to OHT
        kL = 5.90  # minor loss coefficient
        if num2 - elevation_difference > 0:
            A = 10.68 * L / (CHW * (D / 1000) ** 4.87)
            B = 8 * kL / (9.81 * (D / 1000) ** 2)
            q_max = ((num2 - elevation_difference) / (A + B)) ** 0.5
        else:
            q_max = 0
        if flow_unit == 'GPM':
            q_max *= (1 / 6.3e-5)
        elif flow_unit == 'LPS':
            q_max *= 1000
        elif flow_unit == 'LPM':
            q_max *= (1 / 1.67e-5)
        elif flow_unit == 'CMH':
            q_max *= 3600
        else:
            q_max *= 1
        return q_max

    def filter_time_steps(self, num1, num2, num3, arr1):
        """Filtering out unwanted time steps from the hydraulic analysis report
        :num1: ratio of number of time steps reported and number expected
        :num2: total steps reported
        :num3: hydraulic simulation time step in seconds
        :arr1: Time matrix
        :return: list of unwanted time steps
        """
        arr2 = copy.deepcopy(arr1)
        filtered_time_steps = []
        if num1 > 1:
            time = 0
            for step in range(num2):
                if arr2[step] != time:
                    if arr2[step] < time:
                        filtered_time_steps.append(step)
                    elif time < arr2[step] < time + 2 * num3:
                        arr2[step] = time
                        time += num3
                else:
                    time += num3
                    arr2[step] = time
        return filtered_time_steps

    def final_report(self, d, arr1, arr2, arr3, arr4, arr5, arr6):
        """Creating the final report of the hydraulic analysis
        :d: EPANET model
        :arr1: list of unwanted time steps
        :arr2: Time
        :arr3: Pressure
        :arr4: Demand
        :arr5: Flow rate
        :arr6: Tank volume
        :return: list of all outputs
        """
        flow_unit = d.getFlowUnits()
        '''Converting lists to arrays'''
        T_array = np.array(arr2)
        P_array = np.array(arr3)
        D_array = np.array(arr4)
        F_array = np.array(arr5)
        TV_array = np.array(arr6)
        '''Deleting unwanted rows'''
        T = np.delete(T_array, arr1, 0)
        P = np.delete(P_array, arr1, 0)
        D = np.delete(D_array, arr1, 0)
        F = np.delete(F_array, arr1, 0)
        TV = np.delete(TV_array, arr1, 0)
        
        if flow_unit == 'GPM':
            P = np.multiply(P, 0.70325)
            D = np.multiply(D, 6.3e-5)
            F = np.multiply(F, 6.3e-5)
            TV = np.multiply(TV, 0.0283)
        elif flow_unit == 'LPS':
            D = np.multiply(D, (1/ 1000))
            F = np.multiply(F, (1/ 1000))
        elif flow_unit == 'LPM':
            D = np.multiply(D, 1.67e-5)
            F = np.multiply(F, 1.67e-5)
        elif flow_unit == 'CMH':
            D = np.multiply(D,(1/ 3600))
            F = np.multiply(F,(1/ 3600))
        report = [T, P, D, F, TV]
        print("\nFinal report prepared.\n")
        return report
    
    def make_Flow_output(self, d, num1, num2, num3, arr1):
        """Generating the output array for pipe flows
        :d: EPANET model
        :num1: hydraulic simulation time step in seconds
        :num2: demand pattern time step in seconds
        :num3: total number of pattern steps
        :arr1: filtered flow output
        :return: final flow output array
        """
        Flow_out = np.zeros((num3, d.getLinkCount()))
        for i in range(d.getLinkCount()):
            m = int(num2/ num1)
            a = 0
            b = a + m
            for j in range(num3):
                Flow_out[j, i] = np.mean(arr1[a : b, i])
                a += m
                b += m
        Flow_out[Flow_out < 0] = 0
        return Flow_out
    
    def make_TankVolume_output(self, d, num1, num2, num3, arr1):
        """Generating the output array for tank volumes
        :d: EPANET model
        :num1: hydraulic simulation time step in seconds
        :num2: demand pattern time step in seconds
        :num3: total number of pattern steps
        :arr1: filtered tank volume output
        :return: final tank volume output array
        """
        TankVolume_out = np.zeros((num3, d.getNodeTankCount()))
        for i in range(d.getNodeTankCount()):
            m = int(num2/ num1)
            a = 0
            b = a + m
            for j in range(num3):
                TankVolume_out[j, i] = np.mean(arr1[a : b, i])
                a += m
                b += m
        return TankVolume_out
    
    def make_Required_Demand_output(self, d, num1, num2, arr1):
        """Generating the output array for required demands at every node
        :d: EPANET model
        :num1: original number of demand nodes (before network modification)
        :num2: total number of pattern steps
        :arr1: consumer type list
        :return: final array of required nodal demands
        """
        patterns = list(d.getNodeDemandPatternIndex().items())[0][1]
        Required_Demand_out = np.zeros((num2, num1))
        for n in range(num1):
            if arr1[n] != '' and arr1[n] == 'B':
                pattern_id = patterns[n]
                pattern_array = d.getPattern()[pattern_id - 1]
                artificial_consumer_node_index = d.getNodeNameID().index(d.getNodeNameID()[n] + str('-CN')) + 1
                base_demand = list(d.getNodeBaseDemands().items())[0][1][artificial_consumer_node_index - 1]
                m = int(len(pattern_array))
                a = 0
                b = a + m
                for j in range(int(num2/ len(pattern_array))):
                    Required_Demand_out[a: b, n] = np.multiply(pattern_array, base_demand)
                    a += m
                    b += m
        return Required_Demand_out
    
    def compute_demand_deficit(self, d, num1, num2, num3, arr1, arr2, arr3):
        """Compute the demand deficit (%) in every consumer node
        :d: EPANET model
        :num1: original number of demand nodes (before network modification)
        :num2: demand pattern time step in seconds
        :num3: total number of pattern steps
        :arr1: final tank volume output array
        :arr2: final array of required nodal demands
        :arr3: consumer type list
        :return: array of demand deficit (%) in every demand node (-100 value indicate omitted node)
        """
        Demand_deficit_out = np.zeros((num3, num1))
        for n in range(num1):
            if arr3[n] != '' and arr3[n] == 'B':
                artificial_oht_index = d.getNodeTankNameID().index(d.getNodeNameID()[n] + str('-OHT')) + 1
                for j in range(num3):
                    volume_deficit = arr1[j, artificial_oht_index - 1] - arr2[j, n] * (num2/ 1000)
                    if volume_deficit < 0:
                        Demand_deficit_out[j , n] = (abs(volume_deficit) / (arr2[j, n] * (num2/ 1000))) * 100
                    else:
                        Demand_deficit_out[j , n] = 0
            else:
                Demand_deficit_out[: , n] = -100
        return Demand_deficit_out
    
    def compute_relative_distribution(self, d, num1, arr1, arr2, arr3):
        """Compute plot of relative distribution of supply for every node (excluding the omitted nodes)
        :d: EPANET model
        :num1: original number of demand nodes (before network modification)
        :arr1: list of tank outflow pipe names
        :arr2: final flow output array
        :arr3: consumer type list
        return: array of relative distribution in every demand node
        """
        tank_outflow = np.zeros(len(arr2))
        for i in range(len(arr1)):
            tank_out_pipe_index = d.getLinkNameID().index(arr1[i]) + 1
            tank_outflow = np.add(tank_outflow, arr2[:, tank_out_pipe_index - 1])
        Relative_distribution_out = np.zeros((len(arr2), num1))
        for n in range(num1):
            if arr3[n] != '' and arr3[n] == 'B':
                artificial_pipe_to_OHT_index = d.getLinkNameID().index(d.getNodeNameID()[n] + str('-AP_to_OHT')) + 1
                node_withdrawal = arr2[:, artificial_pipe_to_OHT_index - 1]
                Relative_distribution_out[:, n] = np.where(tank_outflow == 0, 0, node_withdrawal/tank_outflow)
            else:
                Relative_distribution_out[: , n] = -100
        return Relative_distribution_out
    
    def make_csv_out(self, arr1, arr2, arr3, arr4, str1):
        """Create CSV outputs
        :arr1: final flow output array
        :arr2: final tank volume output array
        :arr3: array of demand deficit (%) in every demand node (-100 value indicate omitted node)
        :arr4: array of relative distribution in every demand node
        :str1: output folder name
        :return: CSV files
        """
        path = str1
        if os.path.exists(path) != True:
            os.makedirs(path)
        pd.DataFrame(arr1). to_csv(path + '\\Flow')
        pd.DataFrame(arr2). to_csv(path + '\\Tank Volume')
        pd.DataFrame(arr3). to_csv(path + '\\Demand deficit')
        pd.DataFrame(arr4). to_csv(path + '\\Relative distribution')
        
    def check_mass_balance(self, d, num1, arr1, arr2, arr3, arr4):
        """Checking the mass balance of inflows and outflows
        :d: EPANET model
        :num1: original number of demand nodes (before network modification)
        :arr1: list of tank inflow pipe names
        :arr2: list of tank outflow pipe names
        :arr3: final flow output array
        :arr4: consumer type list
        :return: print mass balance results
        """
        net_tank_inflow = 0
        net_tank_outflow = 0
        node_withdrawal = 0
        for i in range(len(arr1)):
            tank_in_pipe_index = d.getLinkNameID().index(arr1[i]) + 1
            net_tank_inflow += sum(arr3[:, tank_in_pipe_index - 1])
        net_tank_inflow = round(net_tank_inflow, 3)
        for i in range(len(arr2)):
            tank_out_pipe_index = d.getLinkNameID().index(arr2[i]) + 1
            net_tank_outflow += sum(arr3[:, tank_out_pipe_index - 1])
        for n in range(num1):
            if arr4[n] != '' and arr4[n] == 'B':
                artificial_pipe_to_OHT_index = d.getLinkNameID().index(d.getNodeNameID()[n] + str('-AP_to_OHT')) + 1
                node_withdrawal += sum(arr3[:, artificial_pipe_to_OHT_index - 1])
        print("Net supply to tank = %.3f m\N{SUPERSCRIPT THREE}/s" % net_tank_inflow)
        print("Net delivery from tank = %.3f m\N{SUPERSCRIPT THREE}/s" % net_tank_outflow)
        print("Net water consumption at the nodes = %.3f m\N{SUPERSCRIPT THREE}/s" % node_withdrawal)
        perc_differnce_consumption = ((node_withdrawal - net_tank_outflow)/ net_tank_outflow) * 100
        print("\nDifference between delivered and consumed = %.3f percent\n" % perc_differnce_consumption)
            
        
class graph:

    def plot_demand_deficit_vs_time(self, d, num1, arr1, arr2, str1):
        """Generate a plot of demand deficit versus time for every node (excluding the omitted node)
        :d: EPANET model
        :num1: original number of demand nodes (before network modification)
        :arr1: output array of demand deficit at every node
        :arr2: consumer type list
        :str1: output folder name
        return: plot of demand deficit versus time
        """
        mpl.rcParams.update({'font.family':'Sans-Serif'})
        x = np.arange(1, len(arr1) + 1)
        for n in range(num1):
            if arr2[n] != '' and arr2[n] == 'B':
                title = "Node " + d.getNodeNameID()[n]
                y = arr1[:, n]
                plt.plot(x, y, marker = 'o', markersize = 2, markerfacecolor = 'gold', markeredgecolor = 'crimson', markeredgewidth = 0.5, linestyle = '--',
                         linewidth = 0.5, color = 'k')
                plt.xticks(np.arange(0, len(arr1) + 1, 48), fontsize = 6)
                plt.yticks(np.arange(0, 110, 20), fontsize = 6)
                plt.ylabel('Demand deficit (%)', fontsize = 8)
                plt.xlabel('Time (h)', fontsize = 8)
                plt.title(title, fontsize = 6, color = 'r')
                path = str1 + '\\'
                if os.path.exists(path) != True:
                    os.makedirs(path)
                fig_name = d.getNodeNameID()[n] + ' Demand_deficit_versus_time.png'
                plt.savefig(path + fig_name, dpi = 600)
                plt.close()
        print("Demand deficit verus time plots created.\n")
        
    def plot_stored_volume_vs_time(self, d, num1, arr1, arr2, str1):
        """Generate a plot of stored water volume versus time for every node (excluding the omitted node)
        :d: EPANET model
        :num1: original number of demand nodes (before network modification)
        :arr1: final tank volume output array
        :arr2: consumer type list
        :str1: output folder name
        return: plot of stored water volume versus time
        """
        mpl.rcParams.update({'font.family':'Sans-Serif'})
        x = np.arange(1, len(arr1) + 1)
        for n in range(num1):
            if arr2[n] != '' and arr2[n] == 'B':
                title = "Node " + d.getNodeNameID()[n]
                artificial_oht_index = d.getNodeTankNameID().index(d.getNodeNameID()[n] + str('-OHT')) + 1
                artificial_oht_diameter = d.getNodeTankData().Diameter[artificial_oht_index - 1]
                artificial_oht_depth = d.getNodeTankData().Maximum_Water_Level[artificial_oht_index - 1]
                if d.getFlowUnits() == 'GPM':
                    artificial_oht_diameter *= 0.0254
                    artificial_oht_depth *= 0.3048
                ymax = math.ceil((math.pi/ 4) * artificial_oht_diameter**2 * artificial_oht_depth)
                y = arr1[:, artificial_oht_index - 1]
                plt.axhline(y = ymax, linestyle = ':', linewidth = 0.5, color = 'b')
                plt.plot(x, y, marker = 'o', markersize = 2, markerfacecolor = 'gold', markeredgecolor = 'crimson', markeredgewidth = 0.5, linestyle = '--',
                         linewidth = 0.5, color = 'k')
                plt.xticks(np.arange(0, len(arr1) + 1, 48), fontsize = 6)
                if ymax <= 5:
                    o = 1
                elif ymax <= 15:
                    o = 3
                elif ymax <= 25:
                    o = 5
                else:
                    o = 6
                plt.yticks(np.arange(0, ymax + o, o), fontsize = 6)
                plt.ylabel('Stored volume in the \nnode overhead tank (m$^{3}$)', fontsize = 8)
                plt.xlabel('Time (h)', fontsize = 8)
                plt.legend(['Overhead tank capacity'], loc = 'best', fontsize = 4)
                plt.title(title, fontsize = 6, color = 'r')
                path = str1 + '\\'
                if os.path.exists(path) != True:
                    os.makedirs(path)
                fig_name = d.getNodeNameID()[n] + ' Stored volume_versus_time.png'
                plt.savefig(path + fig_name, dpi = 600)
                plt.close()
        print("Stored volume verus time plots created.\n")
        
    def plot_required_volume_vs_time(self, d, num1, num2, arr1, arr2, str1):
        """Generate a plot of required water volume versus time for every node (excluding the omitted node)
        :d: EPANET model
        :num1: original number of demand nodes (before network modification)
        :num2: demand pattern time step in seconds
        :arr1: final array of required nodal demands
        :arr2: consumer type list
        :str1: output folder name
        return: plot of required water volume versus time
        """
        mpl.rcParams.update({'font.family':'Sans-Serif'})
        x = np.arange(1, len(arr1) + 1)
        for n in range(num1):
            if arr2[n] != '' and arr2[n] == 'B':
                title = "Node " + d.getNodeNameID()[n]
                y = np.multiply(arr1[:, n], num2/ 1000)
                ymax = np.max(y)
                plt.plot(x, y, marker = 's', markersize = 2, markerfacecolor = 'cyan', markeredgecolor = 'magenta', markeredgewidth = 0.5, linestyle = '--',
                         linewidth = 0.5, color = 'k')
                plt.xticks(np.arange(0, len(arr1) + 1, 48), fontsize = 6)
                if ymax <= 0.1:
                    o = 0.01
                elif ymax <= 0.5:
                    o = 0.05
                elif ymax <= 1:
                    o = 0.1
                else:
                    o = 0.2
                plt.yticks(np.arange(0, ymax + o, o), fontsize = 6)
                plt.ylabel('Required volume for meeting \nnode demands (m$^{3}$)', fontsize = 8)
                plt.xlabel('Time (h)', fontsize = 8)
                plt.title(title, fontsize = 6, color = 'r')
                path = str1 + '\\'
                if os.path.exists(path) != True:
                    os.makedirs(path)
                fig_name = d.getNodeNameID()[n] + ' Required volume_versus_time.png'
                plt.savefig(path + fig_name, dpi = 600)
                plt.close()
        print("Required volume verus time plots created.\n")
    
    def plot_volume_surplus_deficit_vs_time(self, d, num1, num2, arr1, arr2, arr3, str1):
        """Generate a plot of surplus or deficit water volume versus time for every node (excluding the omitted node)
        :d: EPANET model
        :num1: original number of demand nodes (before network modification)
        :num2: demand pattern time step in seconds
        :arr1: final tank volume output array
        :arr2: final array of required nodal demands
        :arr3: consumer type list
        :str1: output folder name
        return: plot of surplus/ deficit water volume in OHT versus time
        """
        mpl.rcParams.update({'font.family':'Sans-Serif'})
        x = np.arange(1, len(arr1) + 1)
        for n in range(num1):
            if arr3[n] != '' and arr3[n] == 'B':
                title = "Node " + d.getNodeNameID()[n]
                artificial_oht_index = d.getNodeTankNameID().index(d.getNodeNameID()[n] + str('-OHT')) + 1
                y1 = arr1[:, artificial_oht_index - 1]
                y2 = np.multiply(arr2[:, n], num2/ 1000)
                y = y1 - y2
                ymin = math.floor(np.min(y))
                ymax = math.ceil(np.max(y))
                plt.plot(x, y, marker = '^', markersize = 3, markerfacecolor = 'w', markeredgecolor = 'r', markeredgewidth = 0.5, linestyle = '--',
                         linewidth = 0.5, color = 'k')
                plt.xticks(np.arange(0, len(arr1) + 1, 48), fontsize = 6)
                if ymax <= 5:
                    o = 1
                elif ymax <= 15:
                    o = 3
                elif ymax <= 25:
                    o = 5
                else:
                    o = 6
                plt.yticks(np.arange(ymin, ymax + o, o), fontsize = 6)
                plt.ylabel('Volume surplus/ deficit in the \nnode overhead tank(m$^{3}$)', fontsize = 8)
                plt.xlabel('Time (h)', fontsize = 8)
                plt.title(title, fontsize = 6, color = 'r')
                path = str1 + '\\'
                if os.path.exists(path) != True:
                    os.makedirs(path)
                fig_name = d.getNodeNameID()[n] + ' Volume surplus or deficit_versus_time.png'
                plt.savefig(path + fig_name, dpi = 600)
                plt.close()
        print("Volume surplus/deficit verus time plots created.\n")
        
    def plot_deficit_percent_vs_time(self, d, num1, arr1, arr2, str1):
        """Generate a plot of deficit water volume percentage versus time for every node (excluding the omitted node)
        :d: EPANET model
        :num1: original number of demand nodes (before network modification)
        :arr1: array of demand deficit (%) in every demand node (-100 value indicate omitted node)
        :arr2: consumer type list
        :str1: output folder name
        return: plot of demand deficit percentrage in node versus time
        """
        mpl.rcParams.update({'font.family':'Sans-Serif'})
        x = np.arange(1, len(arr1) + 1)
        for n in range(num1):
            if arr2[n] != '' and arr2[n] == 'B':
                title = "Node " + d.getNodeNameID()[n]
                y = arr1[:, n]
                plt.plot(x, y, marker = 'v', markersize = 3, markerfacecolor = 'y', markeredgecolor = 'b', markeredgewidth = 0.5, linestyle = '--',
                         linewidth = 0.5, color = 'k')
                plt.xticks(np.arange(0, len(arr1) + 1, 48), fontsize = 6)
                plt.yticks(np.arange(0, 110, 20), fontsize = 6)
                plt.ylabel('Volume deficit in the \nnode overhead tank(%)', fontsize = 8)
                plt.xlabel('Time (h)', fontsize = 8)
                plt.title(title, fontsize = 6, color = 'r')
                path = str1 + '\\'
                if os.path.exists(path) != True:
                    os.makedirs(path)
                fig_name = d.getNodeNameID()[n] + ' Volume deficit percentage_versus_time.png'
                plt.savefig(path + fig_name, dpi = 600)
                plt.close()
        print("Deficit percentage verus time plots created.\n")
        
    def plot_relative_distribution_vs_time(self, d, num1, arr1, arr2, str1):
        """Generate the plot of relative distribution of supply for every node (excluding the omitted nodes)
        :d: EPANET model
        :num1: original number of demand nodes (before network modification)
        :arr1: array of relative distribution in every demand node
        :arr2: consumer type list
        :str1: output folder name
        return: plot of relative distribution of delivered volume in node versus time 
        """
        mpl.rcParams.update({'font.family':'Sans-Serif'})
        x = np.arange(1, len(arr1) + 1)
        for n in range(num1):
            if arr2[n] != '' and arr2[n] == 'B':
                title = "Node " + d.getNodeNameID()[n]
                y = arr1[:, n]
                plt.plot(x, y, marker = 'o', markersize = 2, markerfacecolor = 'orange', markeredgecolor = 'g', markeredgewidth = 0.5, linestyle = '--',
                         linewidth = 0.5, color = 'crimson')
                ymax = round(np.max(y), 1)
                plt.xticks(np.arange(0, len(arr2) + 1, 48), fontsize = 6)
                plt.yticks(np.arange(0, ymax + 0.05, 0.05), fontsize = 6)
                plt.ylabel('Relative distribution of \ndelivered water', fontsize = 8)
                plt.xlabel('Time (h)', fontsize = 8)
                plt.title(title, fontsize = 6, color = 'r')
                path = str1 + '\\'
                if os.path.exists(path) != True:
                    os.makedirs(path)
                fig_name = d.getNodeNameID()[n] + ' Relative distribution_versus_time.png'
                plt.savefig(path + fig_name, dpi = 600)
                plt.close()
        print("Relative distribution verus time plots created.\n")                
                