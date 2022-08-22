"""
author: Kalyan
phase 1: copy the html file in git_folder to your git repo
phase 2: spin up a autoscaling group by creating necessary components 
phase 3: cloning the html file on ec2-instances and placing it in the respective webpage folder 
"""

import boto3
import base64
from botocore.exceptions import ClientError
from botocore.config import Config
import sys
import os
import json
import pprint
import subprocess
import time
import json
import paramiko
import socket


def bash(cmd):
    ps = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    return ps.stdout.read().decode()


class CreateInstanceEC2(object):
    def __init__(self, ec2_client):
        self.ec2_client=ec2_client

    

    def grep_vpc_subnet_id(self):
        try:
            vpc_id = ""
            vpc_list = self.ec2_client.describe_vpcs()
            # print(str(vpc_list))
            for vpc in vpc_list["Vpcs"]:
                # print(str(vpc))
                if (vpc['InstanceTenancy'] == "default"):
                    vpc_id = vpc["VpcId"]
                    # print("--- default VPC ID: "+vpc_id)
                    break

            subnet_list = self.ec2_client.describe_subnets(Filters=[{"Name":"vpc-id", "Values": [vpc_id]}])
            # print(str(subnet_list))
            subnet_id = subnet_list["Subnets"][0]["SubnetId"]
            # print("--- default subnet ID: "+subnet_id)
            az = subnet_list["Subnets"][0]["AvailabilityZone"]
            # print("--- default AZ : "+az)
            return vpc_id, subnet_id, az
        except Exception as e:
            print("!! Exception in 'grep_vpc_subnet_id' = "+str(e))


 


# Lets start the execution from here
try:


    print("\n- STARTED Phase 1 : checking if instance is sshable  ")

    session = boto3.Session(profile_name="default")

    # ec2 = session.client("ec2",config=my_config)
    ec2_client = session.client("ec2")
    ec2_resource = session.resource('ec2')
    # print(ec2.describe_instances())
    # ec2_client = boto3.client('ec2')
    print ("- sessions created ")

    instance_dns = []


    instances = ec2_client.describe_instances()["Reservations"]
    for instance in instances:
        ip=instance['Instances'][0]['PublicDnsName']
        # print (ip)
        if len(ip) > 5:
            instance_dns.append(ip)
            print (ip)
    

    print (instance_dns)
    print("-- Instance details :")
    instances = session.resource('ec2').instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    for instance in instances:
        print ("--- "+str(instance) )  


    for dns in instance_dns: 
        while(1):
            time.sleep(5)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex((dns,22))
            if result == 0:
               print("--- Port 22 is open for "+dns)
               break
            else:
               print("--- Port 22 is not open "+dns)
            sock.close() 


    mongo_dns = instance_dns[0]
    node1_dns = instance_dns[1]
    node2_dns = instance_dns[2]


    # copy script file and start mongodb 
    print ("-- configuring mongodb docker")
    dns = mongo_dns 
    ssh_client=paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    connection = ssh_client.connect(dns, username='ec2-user')  
    print("-- connected to "+dns)
    ftp_client=ssh_client.open_sftp()
    filename = "mongo_ec2_script.sh"
    ftp_client.put(filename,filename)   #for Uploading file from local to remote machine
    print('--- file copied '+filename)
    stdin, stdout, stderr = ssh_client.exec_command('screen -dm bash mongo_ec2_script.sh; sleep 5', get_pty=True)
    output = ""
    for line in stdout.read().splitlines():
        output = output+ "\n"+str(line)
    print("-- executed startup script")
    print("--- output : " +str(connection)+ " : "+ output +" error: "+str(stderr.read().splitlines()) )

    

    # creating the startup script for nodejs server
    cmd = '''
    cp node_ec2_script_template.sh node_ec2_script.sh
    '''

    print(bash(cmd))

    f=open('node_ec2_script.sh', 'r')
    filedata = f.read()

    # print (filedata)
    filedata = filedata.replace('ec2_link',mongo_dns )
    # print (filedata)
    f=open('node_ec2_script.sh', 'w+')
    f.writelines(filedata)
    print("--- node script file modified")
    f.close()
    time.sleep(60)

    
    # copy script file and start nodejs docker 1
    print ("-- configuring nodejs docker 1")
    dns = node1_dns 
    ssh_client=paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    connection = ssh_client.connect(dns, username='ec2-user')  
    print("-- connected to "+dns)
    ftp_client=ssh_client.open_sftp()
    filename = "node_ec2_script.sh"
    ftp_client.put(filename,filename)   #for Uploading file from local to remote machine
    print('--- file copied '+filename)
    stdin, stdout, stderr = ssh_client.exec_command('screen -dm bash node_ec2_script.sh; sleep 5', get_pty=True)
    output = ""
    for line in stdout.read().splitlines():
        output = output+ "\n"+str(line)
    print("-- executed startup script")
    print("--- output : " +str(connection)+ " : "+ output +" error: "+str(stderr.read().splitlines()) )

    
    # copy script file and start nodejs docker 2
    print ("-- configuring nodejs docker 2")
    dns = node2_dns 
    ssh_client=paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    connection = ssh_client.connect(dns, username='ec2-user')  
    print("-- connected to "+dns)
    ftp_client=ssh_client.open_sftp()
    filename = "node_ec2_script.sh"
    ftp_client.put(filename,filename)   #for Uploading file from local to remote machine
    print('--- file copied '+filename)
    stdin, stdout, stderr = ssh_client.exec_command('screen -dm bash node_ec2_script.sh; sleep 5', get_pty=True)
    output = ""
    for line in stdout.read().splitlines():
        output = output+ "\n"+str(line)
    print("-- executed startup script")
    print("--- output : " +str(connection)+ " : "+ output +" error: "+str(stderr.read().splitlines()) )


    #wait until mongodb port is open 
    dns = mongo_dns
    while(1):
        time.sleep(5)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((dns,27017))
        if result == 0:
           print("--- Port 27017 is open for "+dns+" the mongodb server")
           break
        else:
           print("--- Port 27017 is not open for "+dns)
        sock.close()

    #wait until http port is open 
    dns = node1_dns
    while(1):
        time.sleep(5)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((dns,80))
        if result == 0:
           print("--- Port 80 is open for "+dns+" the nodejs server")
           break
        else:
           print("--- Port 80 is not open for "+dns)
        sock.close()


    #wait until http port is open 
    dns = node2_dns
    while(1):
        time.sleep(5)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((dns,80))
        if result == 0:
           print("--- Port 80 is open for "+dns+" the nodejs server")
           break
        else:
           print("--- Port 80 is not open for "+dns)
        sock.close()



    #PRINT ALL success :
    print ("!!! the website is up and running !!!")
    print("-- mongo dns : "+mongo_dns)
    print("-- node dns 1 : "+node1_dns)
    print("-- node dns 2 : "+node2_dns)


    exit()

   
except ClientError as e:
    print(e)

