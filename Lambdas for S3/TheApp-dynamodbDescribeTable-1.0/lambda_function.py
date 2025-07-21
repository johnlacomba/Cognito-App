# This reads in a DynamoDB table name passed to it from the URL queryString 'queryTerm' and returns 
#a list of all Global Secondary Indexes and their Sort Keys (if available).
# The python executes the following steps in order:
# 1. Set up the boto3 client 'dynamodb_client' to connect to dynamoDB
# 2. Execute describe_table() on dynamodb_client with the table name passed to it from the URL queryString
# 3. Append the list of GlobalSecondaryIndexes to outputlist["Response"]
# 4. Return a json.dumps of outputlist

import boto3, json, pprint
from boto3.dynamodb.conditions import Key, Attr
import re

def lambda_handler(event, context):
    # Create the dynamodb client
    dynamodb_client = boto3.client('dynamodb')
    # Set up the json response object to be appended to
    outputlist=json.loads('{"Response":[]}')

    # Write the value of the queryString to the appropriate object
    queryTermfromURL = event['queryStringParameters']['queryTerm']
    # Blacklisted indexes
    blacklistedIndexes = ['devicenonce-index', 'guvid-index', 'virtualstatus-index']
    
    if queryTermfromURL != "":
        # Execute the describe table against table=queryTermfromURL
        queryresponse = dynamodb_client.describe_table(TableName=queryTermfromURL)
        
        # For debugging
        #print(queryresponse)
        
        try:
            # Read the [AttributeName] (primary key) from [KeySchema] from queryresponse
            for response in queryresponse['Table']['KeySchema']:
                # Store the table name values
                keySchema = response.get('AttributeName', [])
                attributeName = response.get('AttributeName', [])
                # Append the index name to outputlist
                outputlist["Response"].append(keySchema)
                # Print it twice (eww) since these are expected to be returned in pairs of ['KeySchema']['AttributeName']
                outputlist["Response"].append(attributeName)
            
            # Read the [GlobalSecondaryIndexes] from queryresponse
            for response in queryresponse['Table']['GlobalSecondaryIndexes']:
                # Store the index value name
                globalSecondaryIndex = response.get('IndexName', [])
                # Check that this index is not blacklisted
                if globalSecondaryIndex not in blacklistedIndexes:
                    # Append the index name to outputlist
                    outputlist["Response"].append(globalSecondaryIndex)
                    # Read the [KeySchema] (sort key) from queryresponse['Table']['GlobalSecondaryIndexes']
                    for keyresponse in response['KeySchema']:
                        # Append the partition key to outputlist
                        outputlist["Response"].append(keyresponse.get('AttributeName', []))
        except Exception as e:
            if re.match(".*KeyError.*GlobalSecondaryIndexes", repr(e)):
                outputlist["Response"].append("No secondary indexes found.")
                pass
            else:
                # Return the error message as the response
                outputlist["Response"].append(repr(e))
                pass
        
        # For debugging
        #print(json.dumps(outputlist['Response']))
    
        responseToReturn = {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            # json.dumps is used to format the output so newlines are properly handled
            "body": json.dumps(outputlist, indent=4)
        }
    
    else:
        responseToReturn = {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.parse('{"Response": "Table name cannot be blank."}')
        }
    # Returns entire response, probably swap with one or more of the 'items' in the response eventually
    return responseToReturn
