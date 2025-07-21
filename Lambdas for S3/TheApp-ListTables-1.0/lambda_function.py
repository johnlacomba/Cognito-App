# This returns a list of all dynamoDB tables in us-east-1 that this account has access to view
#
# The python executes the following steps in order:
# 1. Set up the boto3 client 'dbclient' to connect to dynamoDB
# 2. Execute list_tables() on dbclient
# 3. Append the list of tables to outputlist
# 4. Return a json.dumps of outputlist

import boto3, json, pprint
from boto3.dynamodb.conditions import Key, Attr

def lambda_handler(event, context):
    # Set up the json response object to be appended to
    outputlist=json.loads('{"Response":[]}')

    # Create the dynamodb client to connect with
    dbclient = boto3.client('dynamodb', region_name="us-east-1")
    # Get the list of tables
    tables = dbclient.list_tables()
    # Append the list of tables to outputlist
    outputlist["Response"].append(tables['TableNames'])
    
    # Build the response to return
    responseToReturn = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        # json.dumps is used to format the output so newlines are properly handled
        "body": json.dumps(outputlist, indent=4)
    }
    
    # Return the list of tables
    return responseToReturn
