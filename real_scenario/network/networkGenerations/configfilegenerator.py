import shutil

#Choose the special pedestrian percentage

specPedPer = "H"

# Make sure the value you put here is the last number of demand created + 1
for i in range(20):
    # Make sure to change source
    source = "D:/MASTER THESIS/Practical part/Networks/real_scenario/network/networkGenerations/run_config.sumocfg"
    target = f"D:/MASTER THESIS/Practical part/Networks/real_scenario/network/networkGenerations/demand_12_13_special/config_12_13/run_config_{specPedPer}_{i}.sumocfg"
    # source = "D:/MASTER THESIS/Practical part/Networks/real_scenario/network/networkGenerations/run_config.sumocfg"
    # target = f"D:/MASTER THESIS/Practical part/Networks/real_scenario/network/networkGenerations/demand_12_13/config_12_13/run_config_{i}.sumocfg"
    shutil.copy(source,target)

    # Open file in read mode
    f = open(target, 'r')
    filedata = f.read()
    f.close()
     # Replace string
    newdata = filedata.replace(f'demand_12_13_{specPedPer}_.xml', f'demand_12_13_{specPedPer}_{i}.xml')
    # newdata = filedata.replace(f'demand_12_13_.xml', f'demand_12_13_{i}.xml')
    # Write into file
    f = open(target, 'w')
    f.write(newdata)
    f.close()
