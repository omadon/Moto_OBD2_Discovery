import obd
from tabulate import tabulate


make = 'Honda'
model = 'CRF 300L Rally EU'
# Set to True if you don't trust supported PIDs fields and want to query each PID
QUERY_UNSUPPORTED = False

common_commands = ['ELM_VERSION', 'ELM_VOLTAGE', 'PIDS_A', 'PIDS_B', 'PIDS_C', 'PIDS_9A', 'VIN', 'GET_DTC']

global pids_a, pids_b, pids_c, pids_abc, pids_9a, VIN, dummy_data

def main():
    connection = find_serial()
    get_common_commands(common_commands, connection)
    # Get all Mod 01 commands
    get_mod_commands(1, connection, '1'+ pids_a+ pids_b+ pids_c)
    get_mod_commands(9, connection, '1'+ pids_9a)

def find_serial():
    # Find available serial ports
    ports = obd.scan_serial()         # return list of valid USB or RF ports

    if len(ports) == 0:
        exit("No available serial ports!!!")
        
    print ("Available serial ports:")

    i = 1
    for port in ports:
        print (f'{i}. {port}')
        i+=1   
    selected = int(input("\nEnter desired serial: "))               
    connection = obd.OBD(ports[selected-1]) # connect to the chosen one
    return connection

def get_common_commands(commands, connection):
    table = []
    global pids_a, pids_b, pids_c, pids_9a, VIN
    dummy_data = ''

    for command in commands:
        cmd = obd.commands[command]
        bin_command = cmd.command.decode()
        # Check if command is Mode 0x
        if bin_command[0] == '0':
            mode = cmd.command.decode()[:2]
            pid =  cmd.command.decode()[2:]
        # Probably custom ELM327 command
        else:
            mode = '00'
            pid = bin_command

        response = connection.query(cmd) # send the command, and parse the response
        if not response.is_null():
            value = response.value
            active = 'Yes'
        else:
            value = 'null'
            active = 'No'

        if cmd.name == 'PIDS_A':
            pids_a = format(value.value(0,32),'032b')
        elif cmd.name == 'PIDS_B':
            pids_b = format(value.value(0,32),'032b')
        elif cmd.name == 'PIDS_C':
            pids_c = format(value.value(0,32),'032b')
        elif cmd.name == 'PIDS_9A':
            pids_9a = format(value.value(0,32),'032b')
        elif cmd.name == 'VIN':
            VIN = value.decode()

        table.append([mode, pid, active, cmd.desc, value])

    print ("\n\n-----------", make, "-----------", model, "-----------", "VIN:", VIN, "----------\n\n")
    print (tabulate(table, headers=["Mode", "PID", "Active", "Description", "Value"]))

def get_mod_commands(mod, connection, pid_availability_mask):
    table = []
    value = ''
    # Iterate over every command in Mode 01
    # https://python-obd.readthedocs.io/en/latest/Command%20Tables/
    for cmd in obd.commands[mod]:
        # Extract mode from command object value (b'010A') - first two caracters
        mode = cmd.command.decode()[:2]
        # Extract pid from command object value (b'010A') - last two caracters
        pid =  cmd.command.decode()[2:]

        if pid_availability_mask[int(pid,16)] == '1':
            active = 'Yes'
        else:
            active = 'No'
        
        if active == 'Yes' or QUERY_UNSUPPORTED == True:
            response = connection.query(cmd) # send the command, and parse the response
            if not response.is_null():
                value = response.value
                if cmd.name == 'STATUS_DRIVE_CYCLE':
                    value = str(response.value.MIL) + ', ' + str (response.value.DTC_count) + ', ' + str(response.value.ignition_type)
            else:
                value = 'not supported'
        else:
                value = 'not supported'
        table.append([mode, pid, active, cmd.desc, value])
    print('\n')
    print (tabulate(table, headers=["Mode", "PID", "Active", "Description", "Value"])) 

if __name__ == '__main__':
    main()