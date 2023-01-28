#!/usr/bin/python3.9

def lambda_handler(event, context):
    # here only an error is raised, normally a processing workflow could take place here
    # e.g. the file is downloaded from s3, then processed and a return value is given based on the content
    region = event["region"]
    time = event["time"]
    bucket = event["detail"]["bucket"]["name"]
    file = event["detail"]["object"]["key"]
    raise RuntimeError(f"Hey, something went wrong with your step function... Please check the latest execution! Details: File {file} was uploaded to bucket {bucket} in region {region} at {time}.")