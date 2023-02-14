## Summary

This repository contains a python test file that tests connection attempts against an Azure PrivateLink Endpoint Service that is backed by an Azure NVMe machine.
The python script will execute the following:

1) Setup a PrivateLink endpoint service in resource group A
2) Setup a PrivateLink endpoint and vm in resource group B
3) Create a vm in resource group A and set it up behind the PrivateLink service
4) Install and run `nginx` on the vm behind the PrivateLink service in resource group A
5) Attempt a connection request to the PrivateLink service from the vm in resource group B and record the attempt result
6) Tear down the vm in resource group B
7) Repeat steps 3-6 for `n` number of trials

## Commands

Running the script:

```
python3 test_azure_nvme_privatelink.py
```

## Script Constants

There are a few constants in the script that can be edited in order to adjust things such as the number of trials run or the vm image. 
Note that there are more constants in the scrip than the constants that are listed below. 

**TRIALS** 
Determines the number of times steps 3-6 in the summary above will be run. 

**DEFAULT_IMAGE_NAME**
Determines the type of image that the virtual machines will run.

**PROVIDER_VM_SIZE**
Determines the virtual machine size. Adjust this value to change the type of Azure virtual machine (nvme vs non-nvme).


