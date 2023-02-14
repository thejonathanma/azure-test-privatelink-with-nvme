import subprocess
import json

##### DOCUMENTATION #####

# Run following command to start test:
#    python3 test_azure_nvme_privatelink.py
#
# Please edit the TRIALS variable below to the desired number of trials

TRIALS = 10

##### STATIC CONSTANTS #####

LOCATION = "eastus"
DEFAULT_IMAGE_NAME = "OpenLogic:CentOS:7_9:7.9.2022101800"

PROVIDER_RESOURCE_GROUP_NAME = "jonathan-nvme-pl-provider"
PROVIDER_VNET_NAME = "jonathan-nvme-pl-provider-vnet"
PROVIDER_LB_NAME = "jonathan-nvme-pl-provider-lb"
PROVIDER_PLS_NAME = "jonathan-nvme-pl-provider-service"
PROVIDER_VM_NAME = "jonathan-nvme-pl-provider-vm"
PROVIDER_VM_SIZE = "Standard_L8s_v3"
PROVIDER_LB_NAT_RULE_NAME = "jonathan-nvme-pl-provider-lb-rule"
PROVIDER_LB_NAT_RULE_PORT = 80

CONSUMER_RESOURCE_GROUP_NAME = "jonathan-nvme-pl-consumer"
CONSUMER_VNET_NAME = "jonathan-nvme-pl-consumer-vnet"
CONSUMER_VM_NAME = "jonathan-nvme-pl-consumer-vm"
CONSUMER_VM_SIZE = "Standard_DS1_v2"
CONSUMER_ENDPOINT_NAME = "jonathan-nvme-pl-consumer-endpoint"

##### AZURE CLI HELPER METHODS #####

def run_shell_command(command):
    print ("""Running the following command:\n {0}""".format(command))
    return subprocess.run(
                command, stdout=subprocess.PIPE, shell=True
            ).stdout.decode('utf-8')

def create_resource_group(rg_name):
    raw_command = """
        az group create \
        --location {location} \
        --name {rg_name} \
        --output json \
        --verbose
    """
    command = raw_command.format(location=LOCATION, rg_name=rg_name)
    rg_raw = run_shell_command(command)
    rg_json = json.loads(rg_raw)
    return rg_json

def create_vnet(vnet_name, rg_name):
    raw_command = """
        az network vnet create \
        --name {vnet_name} \
        --resource-group {rg_name} \
        --location {location} \
        --address-prefixes 10.0.0.0/16 \
        --subnet-name default \
        --subnet-prefixes 10.0.0.0/24 \
        --output json \
        --verbose
    """
    command = raw_command.format(
                    vnet_name=vnet_name,
                    location=LOCATION,
                    rg_name=rg_name)
    vnet_raw = run_shell_command(command)
    vnet_json = json.loads(vnet_raw)
    return vnet_json["newVNet"]

def create_load_balancer(lb_name, rg_name, vnet_name):
    raw_command = """
        az network lb create \
        --name {lb_name} \
        --resource-group {rg_name} \
        --sku Standard \
        --location {location} \
        --frontend-ip-zone 1 \
        --vnet-name {vnet_name} \
        --subnet default \
        --output json \
        --verbose
    """
    command = raw_command.format(
                    lb_name=lb_name,
                    rg_name=rg_name,
                    vnet_name=vnet_name,
                    location=LOCATION)
    lb_raw = run_shell_command(command)
    lb_json = json.loads(lb_raw)
    return lb_json["loadBalancer"]

def disable_subnet_pls_policies(rg_name, vnet_name):
    raw_command = """
        az network vnet subnet update \
        --name default \
        --resource-group {rg_name} \
        --vnet-name {vnet_name} \
        --disable-private-link-service-network-policies true \
        --output json \
        --verbose
    """
    command = raw_command.format(rg_name=rg_name, vnet_name=vnet_name)
    run_shell_command(command)

def create_privatelink_service(pls_name, lb_name, rg_name, vnet_name):
    raw_command = """
        az network private-link-service create \
        --name {pls_name} \
        --lb-name {lb_name} \
        --lb-frontend-ip-configs LoadBalancerFrontEnd \
        --resource-group {rg_name} \
        --location {location} \
        --vnet-name {vnet_name} \
        --subnet default \
        --private-ip-allocation-method Dynamic \
        --output json \
        --verbose
    """
    command = raw_command.format(
                    pls_name=pls_name,
                    lb_name=lb_name,
                    rg_name=rg_name,
                    location=LOCATION,
                    vnet_name=vnet_name)
    pls_raw = run_shell_command(command)
    pls_json = json.loads(pls_raw)
    return pls_json

def create_virtual_machine(vm_name, rg_name, vnet_name, vm_size):
    raw_command = """
        az vm create \
        --name {vm_name} \
        --resource-group {rg_name} \
        --image {image} \
        --vnet-name {vnet_name} \
        --subnet default \
        --zone 1 \
        --size {vm_size} \
        --generate-ssh-keys \
        --nic-delete-option delete \
        --os-disk-delete-option delete \
        --output json \
        --verbose
    """
    command = raw_command.format(
                    vm_name=vm_name,
                    rg_name=rg_name,
                    vnet_name=vnet_name,
                    vm_size=vm_size,
                    image=DEFAULT_IMAGE_NAME)
    vm_raw = run_shell_command(command)
    vm_json = json.loads(vm_raw)
    return vm_json

def create_private_endpoint(pe_name, pls_name, pls_id, rg_name, vnet_name):
    raw_command = """
        az network private-endpoint create \
        --name {pe_name} \
        --connection-name {pls_name} \
        --private-connection-resource-id {pls_id} \
        --resource-group {rg_name} \
        --vnet-name {vnet_name} \
        --subnet default \
        --output json \
        --verbose
    """
    command = raw_command.format(
                    pe_name=pe_name,
                    pls_name=pls_name,
                    pls_id=pls_id,
                    rg_name=rg_name,
                    vnet_name=vnet_name)
    pe_raw = run_shell_command(command)
    pe_json = json.loads(pe_raw)
    return pe_json

def open_vm_port(port, rg_name, vm_name):
    raw_command = """
        az vm open-port \
        --port {port} \
        --resource-group {rg_name} \
        --name {vm_name}\
        --output json \
        --verbose
    """
    command = raw_command.format(port=port, rg_name=rg_name, vm_name=vm_name)
    run_shell_command(command)

def run_vm_script(rg_name, vm_name, script):
    raw_command = """
        az vm run-command invoke \
        --resource-group {rg_name} \
        --name {vm_name} \
        --command-id RunShellScript \
        --scripts "{script}" \
        --output json \
        --verbose
    """
    command = raw_command.format(
                    rg_name=rg_name,
                    vm_name=vm_name,
                    script=script)
    print ("""Running the following command on vm {0} in
                resource group {1}:\n {2}""".format(vm_name, rg_name, script))
    response_raw = run_shell_command(command)
    response_json = json.loads(response_raw)
    return response_json

def start_vm_server(rg_name, vm_name):
    script_list = [
        "sudo yum update -y",
        "sudo yum install -y epel-release",
        "sudo yum install -y nginx",
        "sudo systemctl start nginx"
    ]
    for script in script_list:
        run_vm_script(rg_name, vm_name, script)

def create_lb_inbound_nat_rule(rule_name, port, rg_name, lb_name):
    raw_command = """
        az network lb inbound-nat-rule create \
        --name {rule_name} \
        --backend-port {port} \
        --lb-name {lb_name} \
        --protocol Tcp \
        --resource-group {rg_name} \
        --frontend-port {port} \
        --output json \
        --verbose
    """
    command = raw_command.format(
                    rule_name=rule_name,
                    port=port,
                    rg_name=rg_name,
                    lb_name=lb_name)
    nat_rule_raw = run_shell_command(command)
    nat_rule_json = json.loads(nat_rule_raw)
    return nat_rule_json

def associate_inbound_nat_rule_to_vm(
                        rg_name,
                        nat_rule_name,
                        lb_name,
                        nic_name,
                        ip_config_name):
    raw_command = """
        az network nic ip-config inbound-nat-rule add \
        --resource-group {rg_name} \
        --inbound-nat-rule {nat_rule_name} \
        --lb-name {lb_name} \
        --nic-name {nic_name} \
        --ip-config-name {ip_config_name} \
        --output json \
        --verbose
    """
    command = raw_command.format(
                    rg_name=rg_name,
                    nat_rule_name=nat_rule_name,
                    lb_name=lb_name,
                    nic_name=nic_name,
                    ip_config_name=ip_config_name)
    run_shell_command(command)

def get_network_interface(nic_id):
    raw_command = """
        az network nic show \
        --ids {id} \
        --output json \
        --verbose
    """
    command = raw_command.format(id=nic_id)
    nic_raw = run_shell_command(command)
    nic_json = json.loads(nic_raw)
    return nic_json

def get_virtual_machine(rg_name, vm_name):
    raw_command = """
        az vm show \
        --resource-group {rg_name} \
        --name {vm_name} \
        --output json \
        --verbose
    """
    command = raw_command.format(rg_name=rg_name, vm_name=vm_name)
    vm_raw = run_shell_command(command)
    vm_json = json.loads(vm_raw)
    return vm_json

def delete_resource(command_prefix, resource_id):
    raw_command = """
        {command_prefix} delete \
        --ids {id} \
        --yes \
        --output json \
        --verbose
    """
    command = raw_command.format(command_prefix=command_prefix, id=resource_id)
    run_shell_command(command)

def delete_virtual_machine(vm_id):
    delete_resource("az vm", vm_id)

def delete_lb_inbound_nat_rule(rg_name, lb_name, rule_name):
    raw_command = """
        az network lb inbound-nat-rule delete \
        --resource-group {rg_name} \
        --lb-name {lb_name} \
        --name {rule_name} \
        --output json \
        --verbose
    """
    command = raw_command.format(
                    rg_name=rg_name,
                    lb_name=lb_name,
                    rule_name=rule_name)
    run_shell_command(command)

def delete_resource_group(rg_name):
    raw_command = """
        az group delete \
        --name {rg_name} \
        --yes \
        --output json \
        --verbose
    """
    command = raw_command.format(rg_name=rg_name)
    response = run_shell_command(command)
    print (response)

##### SETUP METHODS #####

def setup_provider_resources():
    print ("Setting up resources for the provider resource group.")
    create_resource_group(PROVIDER_RESOURCE_GROUP_NAME)
    create_vnet(PROVIDER_VNET_NAME, PROVIDER_RESOURCE_GROUP_NAME)
    create_load_balancer(
                    PROVIDER_LB_NAME,
                    PROVIDER_RESOURCE_GROUP_NAME,
                    PROVIDER_VNET_NAME)
    disable_subnet_pls_policies(
                    PROVIDER_RESOURCE_GROUP_NAME,
                    PROVIDER_VNET_NAME)
    pls = create_privatelink_service(
                    PROVIDER_PLS_NAME,
                    PROVIDER_LB_NAME,
                    PROVIDER_RESOURCE_GROUP_NAME,
                    PROVIDER_VNET_NAME)
    return pls

def setup_consumer_resources(pls):
    print ("Setting up resources for the consumer resource group.")
    create_resource_group(CONSUMER_RESOURCE_GROUP_NAME)
    create_vnet(CONSUMER_VNET_NAME, CONSUMER_RESOURCE_GROUP_NAME)
    create_virtual_machine(
                    CONSUMER_VM_NAME,
                    CONSUMER_RESOURCE_GROUP_NAME,
                    CONSUMER_VNET_NAME,
                    CONSUMER_VM_SIZE)
    pe = create_private_endpoint(
                    CONSUMER_ENDPOINT_NAME,
                    pls["name"],
                    pls["id"],
                    CONSUMER_RESOURCE_GROUP_NAME,
                    CONSUMER_VNET_NAME)
    return pe

def setup_vm_for_provider_service():
    print ("Setting up vm resources for the provider privatelink service.")
    create_virtual_machine(
                    PROVIDER_VM_NAME,
                    PROVIDER_RESOURCE_GROUP_NAME,
                    PROVIDER_VNET_NAME,
                    PROVIDER_VM_SIZE)
    open_vm_port(80, PROVIDER_RESOURCE_GROUP_NAME, PROVIDER_VM_NAME)
    start_vm_server(PROVIDER_RESOURCE_GROUP_NAME, PROVIDER_VM_NAME)

    create_lb_inbound_nat_rule(
                    PROVIDER_LB_NAT_RULE_NAME,
                    PROVIDER_LB_NAT_RULE_PORT,
                    PROVIDER_RESOURCE_GROUP_NAME,
                    PROVIDER_LB_NAME)

    # the nic and ip-config defaults to this naming convention
    nic_name = PROVIDER_VM_NAME + "VMNic"
    ip_config_name = "ipconfig" + PROVIDER_VM_NAME

    associate_inbound_nat_rule_to_vm(
                    PROVIDER_RESOURCE_GROUP_NAME,
                    PROVIDER_LB_NAT_RULE_NAME,
                    PROVIDER_LB_NAME,
                    nic_name,
                    ip_config_name)

def teardown_vm_for_provider_service():
    print ("Tearing down vm resources for the provider privatelink service.")
    vm_json = get_virtual_machine(
                    PROVIDER_RESOURCE_GROUP_NAME,
                    PROVIDER_VM_NAME)
    vm_id = vm_json["id"]
    delete_virtual_machine(vm_id)
    delete_lb_inbound_nat_rule(
                    PROVIDER_RESOURCE_GROUP_NAME,
                    PROVIDER_LB_NAME,
                    PROVIDER_LB_NAT_RULE_NAME)

def test_pe_connection_request(rg_name, vm_name, pe_ip):
    raw_script = """
        curl -s -o /dev/null -w %{{http_code}} {pe_ip}:80
    """
    script = raw_script.format(pe_ip=pe_ip)
    response = run_vm_script(rg_name, vm_name, script)
    message = response["value"][0]["message"]
    return "200" in message

def test_private_endpoint_connection(consumer_endpoint):
    print ("Setting up resources and testing private endpoint connection.")
    setup_vm_for_provider_service()

    # need to fetch the endpoint private ip off of the endpoint nic
    pe_nic_id = consumer_endpoint["networkInterfaces"][0]["id"]
    pe_nic_json = get_network_interface(pe_nic_id)
    pe_ip = pe_nic_json["ipConfigurations"][0]["privateIpAddress"]

    test_attempts = 3
    attempts = 0
    success = False
    while (attempts < test_attempts):
        success = test_pe_connection_request(
                    CONSUMER_RESOURCE_GROUP_NAME,
                    CONSUMER_VM_NAME,
                    pe_ip)
        if (success):
            break
        attempts += 1

    if (success):
        print ("##################################")
        print ("Connection attempt was successful.")
        print ("Attempts Required: {0}".format(attempts))
        print ("##################################")
    else:
        print ("##################################")
        print ("Connection attempt failed.")
        print ("##################################")

    return success

##### RUN SCRIPT #####

if __name__ == "__main__":
    try:
        provider_pls = setup_provider_resources()
        consumer_endpoint = setup_consumer_resources(provider_pls)

        attempts = 0
        success = 0
        while attempts < TRIALS:
            try:
                is_connection_successful = test_private_endpoint_connection(consumer_endpoint)
                if (is_connection_successful):
                    success += 1
                attempts += 1
            except:
                print("Connection test attempt failed due to an unexpected error. Will try again.")
            finally:
                teardown_vm_for_provider_service()

        delete_resource_group(CONSUMER_RESOURCE_GROUP_NAME)
        delete_resource_group(PROVIDER_RESOURCE_GROUP_NAME)
        print ("Finished test. Successful connection attempts: {0}, Total attempts: {1}".format(success, attempts))
    except:
        print ("Unexpected exception occurred. Deleting resource groups.")
        delete_resource_group(CONSUMER_RESOURCE_GROUP_NAME)
        delete_resource_group(PROVIDER_RESOURCE_GROUP_NAME)
