#!/usr/bin/env python3

import sys
import subprocess
import boto3
import webbrowser

ec2 = boto3.resource('ec2')
s3 = boto3.resource("s3")
s3_client = boto3.client("s3")
# TODO: add cloudwatch

# assignment01-bucket1-$(date +'%F'-'%s')
bucket_name = sys.argv[1]


def main() -> None:
    ec2Setup()
    # s3Setup()

def ec2Setup() -> None:
    """Creates an ec2 instance using the users aws-cli config"""
    # ec2 setup script
    user_data ='''#!/bin/bash
    sudo yum update -y;
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
            # SecurityGroupIds=['sg-002ec529f411873fa'],
            SecurityGroupIds=['assign-sec-group'],
            TagSpecifications=[{
                    'ResourceType': 'instance',
                    'Tags': [{'Key':'Name','Value':'Assignment 01 Server'},]
                }],
            UserData=user_data,
        )
        print ('Waiting until running')
        instance[0].wait_until_running()
        print ('Reloading')
        instance[0].reload()
        print ('Waiting until running')
        instance[0].wait_until_running()
        print ('ec2 instance created.')
    except Exception as error:
        print(error)
        print('Instance creation error')

    try:
        instanceIP = instance[0].public_ip_address
        print ('Instance ID:', instance[0].id, '\nInstance IP:', instanceIP)

        # TODO

        # Adding required files to the instance
        print('Curling image')
        subprocess.run(["ssh -o StrictHostKeyChecking=no ec2-user@" + instanceIP + " 'curl -o image.jpg http://devops.witdemo.net/image.jpg'"],shell=True)
        print('Copying index.html')
        subprocess.run(["scp " + "index.html " + "ec2-user@" + instanceIP + ":/home/ec2-user/index.html"],shell=True)
        # subprocess.run(["ssh " + "ec2-user@" + instanceIP + " 'sudo mv index.html /var/www/html/'"],shell=True)
        print('Moving index.html')
        subprocess.run(["ssh -t ec2-user@" + instanceIP + " 'sudo mkdir /var/www'"],shell=True)
        subprocess.run(["ssh -t ec2-user@" + instanceIP + " 'sudo mkdir /var/www/html'"],shell=True)
        subprocess.run(["ssh -t ec2-user@" + instanceIP + " 'sudo mv ./* /var/www/html'"],shell=True)
    except Exception as error:
        print(error)

    try:
        # TODO
        # Metadata
        # subprocess.run(["ssh ec2-user@" + instanceIP + " 'curl http://" + instanceIP + "/latest/meta-data/local-ipv4 >> index.html'"],shell=True)
        print ('Adding metadata to index file')
        subprocess.run(["ssh ec2-user@" + instanceIP + " 'sudo curl http://169.254.169.254/latest/meta-data/local-ipv4 >> /var/www/html/index.html'"],shell=True)
    except Exception as error:
        print(error)
        print('Metadata')

    try:
        # Monitor
        # TODO
        print ('Copying monitor.sh to instance.')
        subprocess.run(["scp ", "monitor.sh", "ec2-user@" + instanceIP + ":/home/ec2-user/monitor.sh"],shell=True)
        # setting monitor file permissions
        print ('Setting correct permissions')
        subprocess.run(["ssh ec2-user@" + instanceIP + " 'chmod 700 monitor.sh'"],shell=True)
        print ('Running monitor.sh')
        subprocess.run(["ssh -o ec2-user@" + instanceIP + " './monitor.sh'"],shell=True)
    except Exception as error:
        print(error)
        print('Monitoring failed')

    try:
        print ('Opening ec2 website in web browser.')
        webbrowser.open('http://' + instanceIP) # Cross platform
    except Exception as error:
        print(error)
        print('Failed to open website in web browser')


def s3Setup() -> None:
    print ('setting bucket name')
    # bucket_name = 'awdqqueqjdwadd38r2jdwwa'
    for bucket_name in sys.argv[1:]:
        try:
            print ('Creating s3 bucket')
            bucket = s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={
                    'LocationConstraint': 'eu-west-1'
                }
            )
            # print (response)
        except :
            print ('Cannot create bucket.')
        try:
            print ('Setting bucket policy')
            bucket_policy = {
                'Version': '2012-10-17',
                'Statement': [{
                    'Sid': 'AddPerm',
                    'Effect': 'Allow',
                    'Principal': '*',
                    'Action': ['s3:GetObject'],
                    'Resource': "arn:aws:s3:::%s/*" % bucket_name
                }]
            }
            bucket_policy = json.dumps(bucket_policy)
            s3_client.put_bucket_policy(Bucket=bucket_name, Policy=bucket_policy)

            print ('Setting up bucket website')
            s3_client.put_bucket_website(
                Bucket=bucket_name,
                WebsiteConfiguration={
                'ErrorDocument': {'Key': 'error.html'},
                'IndexDocument': {'Suffix': 'index.html'},
                }
            )
        except:
            print ('Cannot setup website.')

        waiter = s3_client.get_waiter('bucket_exists')
        waiter.wait(Bucket=bucket_name)
        # bucket.wait_until_exists()

        filename = ['index.html','error.html']
        print ('Uploading an image to s3 bucket')
        s3.Object(bucket_name,'assign1.jpg').upload_file(Filename='assign1.jpg',ExtraArgs={'ContentType':'image/jpeg'})
        for file in filename:
            try:
                print ('Uploading a file to s3 bucket')
                s3.Object(bucket_name,file).upload_file(Filename=file,ExtraArgs={'ContentType':'text/html'})
                # print(response)
            except Exception as error:
                print (error)
                print('Failed to put file into bucket.')

        print ('Opening s3 website in web browser.')
        webbrowser.open('http://' + bucket_name + '.s3-website-eu-west-1.amazonaws.com')  # Cross platform


if __name__ == "__main__":
    main()
