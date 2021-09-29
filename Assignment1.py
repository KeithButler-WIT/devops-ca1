#!/usr/bin/env python3

# TODO: change from os.system (Depreciated)

import sys
import os
import boto3
import webbrowser

ec2 = boto3.resource('ec2')
s3 = boto3.resource("s3")

# projectx-bucket1-$(date +'%F'-'%s')
bucket_name = sys.argv[1]
# object_name = sys.argv[2]

def main() -> None:
    # createInstance()
    createBucket()
    putInBucket()
    # webbrowser.open('http://ipaddress')  # Cross platform
    # webbrowser.open(url, new=0, autoraise=True)

def createInstance() -> None:
    # ec2 setup script
    user_data ='''#!/bin/bash
    sudo yum install httpd -y;
    sudo systemctl enable httpd;
    sudo systemctl start httpd;
    '''
    print ('Creating the ec2 instance.')
    try:
        instance = ec2.create_instances(
            ImageId = 'ami-0d1bf5b68307103c2',
            MinCount=1,
            MaxCount=1,
            InstanceType='t2.nano',
            KeyName='kbutler_key',
            SecurityGroupIds=['sg-002ec529f411873fa'],
            TagSpecifications=[{
                    'ResourceType': 'instance',
                    'Tags': [{'Key':'Name','Value':'Assignment 01 Server'},]
                }],
            UserData=user_data,
        )
        # instance.wait_until_running()
        print ('ec2 instance created.')
        print ('Instance ID:', instance[0].id)
        print ('Opening ec2 website in web browser.')
        webbrowser.open('http://' + instance.public_ip_address) # Cross platform
    except Exception as error:
        print (error)

def createBucket() -> None:
    print ('Creating the s3 bucket.')
    for bucket_name in sys.argv[1:]:
        try:
            response = s3.create_bucket(
                Bucket=bucket_name, CreateBucketConfiguration={
                    'LocationConstraint': 'eu-west-1'
                }
            )
            # Waits for the bucket to exist
            response = s3.Waiter.BucketExists(bucket=bucket_name)
            print ('s3 bucket created.')
            print (response)
        except Exception as error:
            print (error)

def putInBucket() -> None:
    try:
        # Sets the s3 bucket as a static website
        print ('Enabling website functionality.')
        response = s3.BucketWebsite(bucket_name)
        # Downloads the required image
        print ('Downloading required files.')
        os.system('wget http://devops.witdemo.net/assign1.jpg')
        # Adds two files from the current directory  to the s3 bucket
        print ('Sending files to s3 bucket.')
        response = s3.Object(bucket_name, 'assign1.jpg').put(Body=open('assign1.jpg', 'rb'))
        print (response)
        response = s3.Object(bucket_name, 'index.html').put(Body=open('index.html', 'rb'))
        print (response)
        print ('Opening s3 website in web browser.')
        webbrowser.open('http://' + bucket_name + '.s3-website-eu-west-1.amazonaws.com')  # Cross platform
        print (response)
        print ('Removing unneaded file from host computer.')
        os.system('rm assign1.jpg') # Cleaning up directory
    except Exception as error:
        print (error)


if __name__ == "__main__":
    main()
