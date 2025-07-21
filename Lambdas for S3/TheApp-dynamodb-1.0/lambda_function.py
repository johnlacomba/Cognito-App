# This takes values passed to it in URL queryStrings and executes a query against the given DynamoDB Table and Secondary Index.
# To handle obfuscation of sensitive fields the lines within the response (queryresponse['Items']) are parsed and any responsekeys matching items defined in redactList[] 
#have that key's value stripped out of the response.
#
# The python executes the following steps in order:
# 1. Set up the boto3 client 'dynamodb' to connect to dynamoDB
# 2. Read in the string to query for; as well as the index, partitionKey, and table to query
# 2. Execute query() on the table object using the Global Secondary Index
# 3. Iterate over the responseKeys of queryresponse['Items'] and obfuscate any values for responseKeys that match items defined in redactList[]
# 4. Append the obfuscated query response to outputlist["Response"]
# 4. Return a json.dumps of outputlist

import boto3, json
from boto3.dynamodb.conditions import Key, Attr
import re

def lambda_handler(event, context):
    # Get the service resource.
    dynamodb = boto3.resource('dynamodb')
    keylist=json.loads('{"Response":[]}')
    outputlist=json.loads('{"Response":[]}')
    
    # Write the values of the queryStrings to their appropriate objects
    queryTermfromURL = event['queryStringParameters']['queryTerm']
    indexNamefromURL = event['queryStringParameters']['indexName']
    partitionKeyfromURL = event['queryStringParameters']['partitionKey']
    tableNamefromURL = event['queryStringParameters']['tableName']
    
    # Read in the scopes passed to this function
    theScopes = event['requestContext']['authorizer']['claims']['scope']
    
    # Log information about the user calling this Lambda
    print("Username making this request:", event['requestContext']['authorizer']['claims']['username'], ", Log Index:", event['queryStringParameters']['indexName'], ", Partition Key:", event['queryStringParameters']['partitionKey'], ", Table:", event['queryStringParameters']['tableName'])
    
    # Instantiate a table resource object without actually
    # creating a DynamoDB table. Note that the attributes of this table
    # are lazy-loaded: a request is not made nor are the attribute
    # values populated until the attributes
    # on the table resource are accessed or its load() method is called.
    table = dynamodb.Table(tableNamefromURL)
    
    if queryTermfromURL != "":
        # Notes about query: A single Query operation can retrieve a maximum of 1 MB of data. This limit applies before any FilterExpression or ProjectionExpression is applied to the results.
        # If LastEvaluatedKey is present in the response and is non-null, you must paginate the result set.
        
        # Check to see if the indexNamefromURL contains the word "index"
        # The IndexName must be left blank if this is a primary index, and included if it's a secondary index
        if re.match(".*-index", repr(indexNamefromURL)):    
            # Execute the query in the format for the secondary index
            queryresponse = table.query(
                TableName=tableNamefromURL, #'Dev_Aepa',
                IndexName=indexNamefromURL, #'accountno-index'
                #ProjectionExpression='', # ProjectionExpression was causing errors when the 'status' and/or 'region' fields were included
                # Query using a secondary index instead of the primary
                # https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/LegacyConditionalParameters.KeyConditions.html
                KeyConditionExpression=partitionKeyfromURL+' = :userVal',  #'accountno'
                ExpressionAttributeValues={
                ':userVal': queryTermfromURL
                }
            )
        else:
            # Execute the query in the format for the primary index
            queryresponse = table.query(
                TableName=tableNamefromURL, #'Dev_Aepa',
                #ProjectionExpression='', # ProjectionExpression was causing errors when the 'status' and/or 'region' fields were included
                # Query using a secondary index instead of the primary
                # https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/LegacyConditionalParameters.KeyConditions.html
                KeyConditionExpression=partitionKeyfromURL+' = :userVal',  #'accountno'
                ExpressionAttributeValues={
                ':userVal': queryTermfromURL
                }
            )
        
        # List of items to redact from the output
        #redactList = ['encryptedpassword', 'userpassword', 'givenname', 'sn', 'devicenoncesigningkey', 'userpassword']
            
        # For debugging
        #outputlist["Response"].append(queryresponse['Items'])
        #outputlist["Response"].append(repr(queryresponse['Items']))
        
        # Redact required items from the response
        obfuscationMessage = "REDACTED"
        for item in queryresponse["Items"]:
            if "encryptedpassword" in item:
                item["encryptedpassword"] = obfuscationMessage
            if "userpassword" in item:
                item["userpassword"] = obfuscationMessage
            if "givenname" in item:
                item["givenname"] = obfuscationMessage
            if "sn" in item:
                item["sn"] = obfuscationMessage
            if "userpassword" in item:
                item["userpassword"] = obfuscationMessage
            if "encryptedpassword" in item:
                item["encryptedpassword"] = obfuscationMessage
            # Check the scopes passed to the lambda to determine if the nonce should be obfuscated
            if "mainapi/nonce" not in theScopes:
                if "devicenoncesigningkey" in item:
                    item["devicenoncesigningkey"] = obfuscationMessage
            
#        try:
#            # For each Item from queryresponse
#            for response in queryresponse['Items']: 
#                for responsekey in response:    # this is done because queryresponse['Items'] is a list of dict's
#                    # Read in the items to redact
#                    for redactString in redactList:
#                        # Check each redactString in redactList against the responsekey
#                        if redactString in responsekey:
#                            # Clear the response[responsekey]
#                            response[responsekey]=''
#                            # After we've found a match exit this loop to save cycles
#                            break
#                    # Append outputlist["Response"] with the response key and value 
#                    outputlist["Response"].append(repr({responsekey: response[responsekey]}))
#                #outputlist["Response"].append("--------------------")
#        except Exception as e:
#            # Return the error message as the response
#            outputlist["Response"].append(repr(e))
#            pass
    
        responseToReturn = {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            # json.dumps is used to format the output so newlines are properly handled
            "body": json.dumps(queryresponse, indent=4, separators=(',', ': '))
        }
    
    else:
        responseToReturn = {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.parse('{"Response": "Field cannot be blank."}')
        }
    # Returns entire response, probably swap with one or more of the 'items' in the response eventually
    return responseToReturn
