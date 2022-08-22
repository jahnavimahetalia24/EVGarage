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


sg_name = "awspy_security_group"



class CreateInstanceEC2(object):
    def __init__(self, ec2_client):
        self.ec2_client=ec2_client


    def create_ec2_security_group(self):
        global sg_name
        print("--- STARTED : Creating the Security Group {}  ".format(sg_name))
        try:
            vpc_id, subnet_id, az = self.grep_vpc_subnet_id()
            response = self.ec2_client.create_security_group(
                GroupName=sg_name,
                Description="This SG is created using Python",
                VpcId=vpc_id
            )
            sg_id = response["GroupId"]
            print("--- security group id = "+sg_id)
            sg_config = self.ec2_client.authorize_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort':22,
                        'IpRanges':[{'CidrIp':'0.0.0.0/0'}]
                    },
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 80,
                        'ToPort': 80,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            )
            print("---- DONE: Created the Security Group {} : configured - Security Group ID: {} ".format(sg_name, sg_id))
            return sg_id, sg_name
        except Exception as e:
            if str(e).__contains__("already exists"):
                response = self.ec2_client.describe_security_groups(GroupNames=[sg_name])
                sg_id = response["SecurityGroups"][0]["GroupId"]
                print("Security Group {} already exists with Security Group ID: {} ".format(sg_name, sg_id))
                return sg_id, sg_name
            else :
                print("!! Exception in 'create_ec2_security_group' = "+str(e))

    def check_launch_template_id(self,template_name):
        #check if it exists, if yes return id 
        try:
            launch_template_list = self.ec2_client.describe_launch_templates(
                LaunchTemplateNames=[
                    template_name,
                ]
            )
            # print(str(launch_template_list))
            template_id = launch_template_list['LaunchTemplates'][0]['LaunchTemplateId']
            print("----- launch template : "+template_name+" | "+template_id+" already exists")
            return template_id
        except Exception as e:
            if "NotFoundException" in str(e):
                print ("----- launch template : "+template_name+" not found ")
            else :
                print("!! Exception in 'check_launch_templates' : "+str(e))
            return False


    def create_ec2_launch_template(self):
        print("-- STARTED: Creating the Launch Templates ")
        template_name = 'awspy_launch_template'

        if(self.check_launch_template_id(template_name)):
            self.ec2_client.delete_launch_template(
                LaunchTemplateName=template_name
                )
            print(" --- deleting the exisiting template for "+template_name)

        try:
            sg_id, sg_name = self.create_ec2_security_group() # creates security group

            time.sleep(10)# delay to ensure that the existing template is deleted 
            response = self.ec2_client.create_launch_template( # creates launch template
                LaunchTemplateName=template_name,
                LaunchTemplateData={
                    'ImageId': "ami-085284d24fe829cd0",
                    'InstanceType' : "t2.micro",
                    'KeyName' : "default key pair",
                    'UserData': USERDATA_B64,
                    'SecurityGroupIds': [sg_id]
                },
                VersionDescription='WebVersion1'
            )
            template_id = response['LaunchTemplate']['LaunchTemplateId']
            print("--- DONE: Creating the Launch Templates : COMPLETED : TemplateID:{}, TemplateName:{}".format(template_id, template_name ))
            return template_id, template_name
        except Exception as e:
            print("!! Exception in 'create_ec2_launch_template'= "+str(e))
            response = self.ec2_client.describe_launch_templates(
                LaunchTemplateNames=[
                    template_name,
                ]
            )
            template_id = response['LaunchTemplates'][0]['LaunchTemplateId']
            return template_id, template_name

    def create_ec2_auto_scaling_group(self):
        print ("- STARTED: creation of Auto Scaling Group using Launch Templates ")
        launch_template_id, launch_template_name = self.create_ec2_launch_template()
        vpc_id, subnet_id, az = self.grep_vpc_subnet_id()

        client = boto3.client('autoscaling')
        response = client.create_auto_scaling_group(
            AutoScalingGroupName='awspy_autoscaling_group',
            LaunchTemplate={
                'LaunchTemplateId': launch_template_id,
            },
            MinSize=2,
            MaxSize=3,
            DesiredCapacity=2,
            AvailabilityZones=[
                az,
            ]
        )

        if str(response["ResponseMetadata"]["HTTPStatusCode"]) == "200":
            print("-- DONE: Creation of Auto Scaling Group using Launch Templates ----")
        else:
            print("-- FAILED: Creation of Auto Scaling Group using Launch Templates ----")
        return True




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


    def print_vpc_subnet_id(self):
        try:
            vpc_id = ""
            vpc_list = self.ec2_client.describe_vpcs()
            # print(str(vpc_list))
            for vpc in vpc_list["Vpcs"]:
                # print(str(vpc))
                if (vpc['InstanceTenancy'] == "default"):
                    vpc_id = vpc["VpcId"]
                    print("--- default VPC ID: "+vpc_id)
                    break

            subnet_list = self.ec2_client.describe_subnets(Filters=[{"Name":"vpc-id", "Values": [vpc_id]}])
            # print(str(subnet_list))
            subnet_id = subnet_list["Subnets"][0]["SubnetId"]
            print("--- default subnet ID: "+subnet_id)
            az = subnet_list["Subnets"][0]["AvailabilityZone"]
            print("--- default AZ : "+az)
        except Exception as e:
            print("!! Exception in 'print_vpc_subnet_id' = "+str(e))


def ensure_default_vpc(ec2_client_obj):
    try:
        vpc = ec2_client_obj.create_default_vpc()
        print("-- default VPC created "+str(vpc["Vpc"]))
    except ClientError as e:
        print("!! exception in 'create_default_vpc'= "+str(e))
        vpc =  ec2_client_obj.describe_vpcs()
        if (vpc['Vpcs'][0]['InstanceTenancy'] == "default"):
            vpc_id = vpc['Vpcs'][0]['VpcId']
            print("-- default instance with vpc id = '"+vpc_id+"' already exists")
        else :
            print("the follwing instances exist = "+str(vpc))
    return vpc

def delete_autoscaling():
    try:
        client = boto3.client('autoscaling')
        client.delete_auto_scaling_group(
            AutoScalingGroupName='awspy_autoscaling_group',
            ForceDelete=True,
        )
        print("-- autoscaling group deletion started") 
        time.sleep(30)
        autoscale_describe = client.describe_auto_scaling_groups(AutoScalingGroupNames=['awspy_autoscaling_group'],)
        print("--- "+client.describe_auto_scaling_groups(AutoScalingGroupNames=['awspy_autoscaling_group'],)['AutoScalingGroups'][0]['AutoScalingGroupName']+" is still being deleted")
        while (1):
            if ( not (client.describe_auto_scaling_groups(AutoScalingGroupNames=['awspy_autoscaling_group'],)['AutoScalingGroups'][0]['AutoScalingGroupName'] == "awspy_autoscaling_group")  ):
                break
            # autoscale_describe = client.describe_auto_scaling_groups(AutoScalingGroupNames=['awspy_autoscaling_group'],)
            print("--- "+client.describe_auto_scaling_groups(AutoScalingGroupNames=['awspy_autoscaling_group'],)['AutoScalingGroups'][0]['AutoScalingGroupName']+" still being deleted ...")
            time.sleep(5)

        # print("<program ending>")
        # exit()
    except Exception as e:
        print("-- autoscaling group unable to delete "+str(e))
        # print("<program ending>")
        # exit()

def delete_vpcs(ec2_client_obj):
    try: 
        delete_autoscaling()
        vpc =  ec2_client_obj.describe_vpcs()
        if (vpc['Vpcs'][0]['InstanceTenancy'] == "default"):
            vpc_id = vpc['Vpcs'][0]['VpcId']
            ec2_client_obj.delete_vpc(
                    VpcId=vpc_id,
                    )
            print("-- deleting VPC with vpc id = '"+vpc_id+"' ")
        else :
            print("-- instance not found for deleting ")
        time.sleep(30)
    except Exception as e:
        print("-- vpc unable to delete, Exception= "+str(e))




# Lets start the execution from here
try:

    # Commands to push the html into git 
    # cmd='''
    # cd /home/iadt/final_pro/EVGarage-main/EVGarage-main_v2/Infrastructure;
    # terraform init; terraform apply -auto-approve;
    # '''

    # print(bash(cmd))

    print("\n- STARTED Phase 2 : checking if instance is sshable  ")

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


    print("-- Instance details :")
    instances = session.resource('ec2').instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    for instance in instances:
        print (instance)   


    node_dns = instance_dns[0]
    mongo_dns = instance_dns[1]


    cmd = '''
    cp node_ec2_script_template.sh node_ec2_script.sh
    '''

    print(bash(cmd))

    f=open('node_ec2_script.sh', 'r')
    filedata = f.read()

    print (filedata)
    filedata = filedata.replace('ec2_link',mongo_dns )
    print (filedata)
    f=open('node_ec2_script.sh', 'w+')
    f.writelines(filedata)
    print("--- node script file modified")
    f.close()


    # ftp_client.close()

    # copy script file and start mongodb 
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
    print("-- output : " +str(connection)+ " : "+ output +" error: "+str(stderr.read().splitlines()) )

    #wait until mongodb port is open 
    while(1):
        time.sleep(5)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((dns,27017))
        if result == 0:
           print("--- Port 27017 is open for "+dns)
           break
        else:
           print("--- Port 27017 is not open for "+dns)
        sock.close()


    # copy script file and start nodejs
    dns = node_dns 
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
    print("-- output : " +str(connection)+ " : "+ output +" error: "+str(stderr.read().splitlines()) )

    #wait until http port is open 
    while(1):
        time.sleep(5)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((dns,80))
        if result == 0:
           print("--- Port 80 is open for "+dns)
           break
        else:
           print("--- Port 80 is not open for "+dns)
        sock.close()


    # run ansible playbook for nodejs


    #PRINT ALL IPS :
    print("-- node dns : "+node_dns)
    print("-- mongo dns : "+mongo_dns)


    # f=open('node_ec2_script.sh', 'r')
    # print(f.read())



    exit()

    instance_dns =[]
    print("-- Instance details :")
    instances = session.resource('ec2').instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    for instance in instances:
        print (instance)   
    exit

    # while(1):
    #     i=0
    #     time.sleep(5)
    #     try:
    #         print("checking")
    #         instances = session.resource('ec2').instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    #         for instance in instances:
    #             nwip = instance.network_interfaces_attribute[0]['Association']['PublicDnsName']
    #             i+=1
    #         if i == 2:
    #             for instance in instances:
    #                 instance_dns.append(instance.network_interfaces_attribute[0]['Association']['PublicDnsName'])
    #                 print( "--- instance ",instance.id, instance.instance_type, instance.network_interfaces_attribute[0]['Association']['PublicDnsName'])
    #             break
    #     except Exception as e:
    #         print ("!! exception trying again ")
    # print ("-- Instance DNS: ")
    # for dns in instance_dns:
    #     print("--- "+dns)


    # for dns in instance_dns: 
    #     while(1):
    #         sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         result = sock.connect_ex((dns,22))
    #         if result == 0:
    #            print("--- Port 22 is open for "+dns)
    #            break
    #         else:
    #            print("--- Port 22 is not open "+dns)
    #         sock.close()

    # time.sleep(60)
    # for dns in instance_dns: 
    #     ssh_client=paramiko.SSHClient()
    #     ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    #     connection = ssh_client.connect(dns, username='ubuntu', key_filename='aws_default_key_pair.pem')  
    #     print("-- connected to "+dns)
    #     stdin, stdout, stderr = ssh_client.exec_command('if [ -d "iadt_git" ] ; then     rm -rf "iadt_git"; fi; git clone --branch user_test https://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@github.com/Kalyan96/iadt_git;sudo rm -rf /var/www/html/index.html;sudo cp iadt_git/simple.html /var/www/html/index.html;sudo service apache2 restart;', get_pty=True)
    #     output = ""
    #     for line in stdout.read().splitlines():
    #         output = output+ "\n"+str(line)
    #     print("-- output : " +str(connection)+ " : "+ output +" error: "+str(stderr.read().splitlines()) )

    # for dns in instance_dns:
    #     print ("access urls = http://"+dns)
    # print("\n- Executed")
        
 


    # ftp_client=ssh_client.open_sftp()
    # ftp_client.put(‘localfilepath’,remotefilepath’)   #for Uploading file from local to remote machine
    #ftp_client.get(‘remotefileth’,’localfilepath’)   for Downloading a file from remote machine

    # ftp_client.close()






    # print(ec2_client.describe_instances())
    # for vpc in ec2_client.describe_instances()['Reservations'][0]['Instances']['PublicDnsName']:
    # print( "--- instance details : "+str( vpc. )  )
    # print("- DONE Phase 2 : initialising AWS ")


    # CreateInstanceEC2(ec2_client).check_launch_template_id("awspy_launch_tesmplate")


    # alb_sec_group_name = 'alb-sg'
    # launch_config_name = 'web-lc'
    # auto_scaling_group_name = 'web-asg'
    # scale_up_name = 'scale_up'
    # scale_down_name = 'scale_down'


    # vpc = boto3.resource('ec2').create_vpc(CidrBlock='10.0.0.0/16', AmazonProvidedIpv6CidrBlock=True)
    # vpc.create_tags(Tags=[{"Key": "Name", "Value": "iadt_vpc"}])



    # subnet_id = subnet.id
    # subnet2_id = subnet2.id
    # print(vpc_id)
    # print(subnet_id)
    # print(subnet2_id)


    
    # CreateInstanceEC2(ec2_client).grep_vpc_subnet_id()

    # call_obj = CreateInstanceEC2(ec2_client)
    # call_obj.create_ec2_auto_scaling_group()
except ClientError as e:
    print(e)


