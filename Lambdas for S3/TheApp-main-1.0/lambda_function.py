# This builds the main page that makes the calls out to DynamoDB, it uses the access_token from sessionStorage.
# The python is responsible for editing the javascript inside the HTML body and 
#replaces the following strings with the values from the relevant lambda environment variables:
#userpooldomain, theregion, userpoolclientid, apiid, stagename.
#

import os

def lambda_handler(event, context):
    # Read in the environment variables
    userpooldomain = os.environ['userpooldomain']
    theregion = os.environ['theregion']
    userpoolclientid1 = os.environ['userpoolclientid1']
    userpoolclientid2 = os.environ['userpoolclientid2']
    apiid = os.environ['apiid']
    stagename = os.environ['stagename'].lower()
    
    # Read in the scopes passed to this function
    theScopes = event['requestContext']['authorizer']['claims']['scope']
    
    # Build the dynamoDB table prefix from the stagename, for use in the calls to callDynamoDB()
    if stagename == "sit" or stagename == "dev":
        dyntableprefix = "dev"
    elif stagename == "perf":
        dyntableprefix = "prf"
    elif stagename == "prod":
        dyntableprefix = "prd"
    
    responseToReturn = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html"
        },
        "body": """<!DOCTYPE html>
<html>

<body>

<style type="text/css">
    
    body{
        background:darkslateblue;
    }
    
    #div-title1 {
        white-space:nowrap;
        overflow-x:auto;
    } 
    
    #theapplogo {
        background: #000;
        margin-top:-40px;
    }
    
    #logoline {
        margin-left: auto;
        margin-right: auto;
        width:100%;
        height:40px;
        background:black;
    }
    
    .centerlogo {
        display: block;
        margin-left: auto;
        margin-right: auto;
        max-width: 100%;
        max-height: 40px;
        text-align: center;
    }
    
    .centerborder {
        display: block;
        margin-left: auto;
        margin-right: auto;
        text-align: center;
        max-width: 80%;
        border: 3px solid black;
        background:silver;
    }
    
    textarea {
        width: 240px;
        height: 16px;
        overflow: hidden;
        resize: none;
    }
    
    .result {
        white-space:pre-wrap;
        text-align: left;
    }
    
    .heading {
        text-align: center;
        font-size: 1.5em;
    }
    
    hr.border {
        border: 0.3em solid black;
    }

    #loadingOverlay {
        position: fixed; /* make it fixed to the window */
        top: 0; /* position from the top of the window */
        left: 0; /* position from the left of the window */
        width: 100%; /* cover the entire window */
        height: 100%; /* cover the entire window */
        background-color: rgba(0, 0, 0, 0.5); /* semi-transparent black background */
        display: flex; /* use flexbox to center the content */
        justify-content: center; /* center horizontally */
        align-items: center; /* center vertically */
        z-index: 999; /* make it appear over everything */
        display: none; /* start invisible */
      }
    
    #loadingOverlay-content {
        width: 40px;
        height: 40px;
        background-color: black;
        color: white;
        border-radius: 50%;
        border: 10px solid transparent;
        border-top-color: black;
        animation: rotate 0.66s linear infinite;
        display: none; /* start invisible */
        justify-content: center;
        align-items: center;
      }

    @keyframes rotate {
      0% {
        transform: rotate(0deg);
      }
      100% {
        transform: rotate(360deg);
      }
    }
    
</style>

<!-- This line prevents 403 errors for the favicon.ico when loading the page -->
<link rel="icon" href="data:;base64,iVBORw0KGgo=">

<div id="loadingOverlay">
    <div id="loadingOverlay-content">
        <p>theapp</p>
    </div>
</div>

<div id="logoline"></div>

<img class="centerlogo" id=theapplogo src="LOGO_URL"></img>

<!-- NOTE: indexList starts empty because the header is defined in postDescribeTable() -->
<div class="centerborder">
    <div id="manualHeader" class="heading">Query by table and index</div>
    
    <select id = "tableList" onfocus = "document.getElementById('indexList').selectedIndex=0;">
        <option> ---Choose table name--- </option>
    </select>
    
    <select id = "indexList" >
    </select>
    
    <div id="div-title1">
        <a id="queryType">Query by "partition key":</a>
        <textarea id="queryInputManual"></textarea>
    </div>
    
    <div>
        <button id="submitManual" type="submit">Submit</button>
    </div>
    
    <div id="resultManual" class="result"></div>
</div>

<hr class="border"></hr>

<div class="centerborder">
    <div id="snapshotHeader" class="heading">360L Radio Snapshot Tool</div>

    <div id="div-title1">
        <a id="queryType">Query by the RadioID:</a>
        <textarea id="queryInput"></textarea>
    </div>
    
    <div>
        <button id="submit" type="submit">Submit</button>
    </div>
    
    <div id="01" class="result"></div>
    <div id="02" class="result"></div>
    <div id="03" class="result"></div>
    <div id="04" class="result"></div>
    <div id="05" class="result"></div>
    <div id="06" class="result"></div>
    <div id="07" class="result"></div>
    <div id="08" class="result"></div>
</div>

<script id="executeQuery" type="text/javascript">
    // Declare some global vars
    let lines, linesTable;
    let sortKey;
    let indexList = document.getElementById("indexList");
    let tableList = document.getElementById("tableList");
    let tableBlacklist = ["prd-tenfoot", "prd-oactrust", "prd-k2refreshtokenlink", "terraform-state-table", "terraform-state-lock-table"];
    let targetTable;    // This is changed in the chooseTable function
    
    // All of this is needed to dynamically resize the textarea as it's populated
    let textarea = document.getElementById("queryInput");
    let tael = textarea.addEventListener.bind(textarea);
    let autoResizeTextArea = (e) => {
        const element = e.target
        element.style.height = 'auto'
        element.style.height = '16px'
        element.style.overflowY = 'hidden'
        element.style.height = element.scrollHeight + 'px'
    }
    tael('update', autoResizeTextArea);
    tael('keyup', autoResizeTextArea);
    
    // All of this is needed to dynamically resize the textarea queryInputManual as it's populated
    let textareaM = document.getElementById("queryInputManual");
    let taelM = textareaM.addEventListener.bind(textareaM);
    let autoResizeTextAreaM = (e) => {
        const elementM = e.target
        elementM.style.height = 'auto'
        elementM.style.height = '16px'
        elementM.style.overflowY = 'hidden'
        elementM.style.height = elementM.scrollHeight + 'px'
    }
    taelM('update', autoResizeTextArea);
    taelM('keyup', autoResizeTextArea);
    
    
    
    // Set up the onChange event to set up the tableList select element
    tableList.onchange = async function(){
        await onChangeChooseTable();
        await onChangeChooseTableSetIndexList();
    }
    // Set up the onChange event to set up the indexList select element
    indexList.onchange = chooseIndex;
    
    // This is to set the text area to click the submit button when hitting enter (and not holding shift)
    document.getElementById("queryInput")
    .addEventListener("keyup", function(event) {
        event.preventDefault();
        if (event.keyCode === 13 && ! event.shiftKey) {
            // Remove the newline that was added when the user pressed Enter
            queryInput.value = queryInput.value.substring(0,queryInput.value.length-1);
            // Submit the POST
            document.getElementById("submit").click();
        }
    });
    document.getElementById("queryInputManual")
    .addEventListener("keyup", function(event) {
        event.preventDefault();
        if (event.keyCode === 13 && ! event.shiftKey) {
            // Remove the newline that was added when the user pressed Enter
            queryInputManual.value = queryInputManual.value.substring(0,queryInputManual.value.length-1);
            // Submit the POST
            document.getElementById("submitManual").click();
        }
    });
    
    // Used by tableList.onchange to define a promise for the responses from chooseTable() and postDescribeTable() 
    function onChangeChooseTable() {
        return new Promise(async function (resolve, reject) {
            await chooseTable();
            // Re-run postDescribeTable() with the updated table name
            await postDescribeTable();
            resolve();
        })
    }
    
    // Used by tableList.onchange to call chooseIndex(), or to handle clearing the page elements
    function onChangeChooseTableSetIndexList(){
        return new Promise(function (resolve, reject) {
            indexList.selectedIndex = 0;
            indexName = indexList.options[indexList.selectedIndex].text;
            
            // Force the first secondary index returned to be used.  This is done because when only one secondary index is returned the onChange event cannot fire.
            // Check that a secondary index was returned before setting the secondary index
            if ( indexName != 'No secondary indexes found.' ) {
                //chooseIndex();
            } else {
                // Clear the text of the queryType element
                document.getElementById("queryType").text = 'Query by "partition key":';
                // Clear the placeholder text of the queryInputManual element
                document.getElementById("queryInputManual").placeholder = "";
                // Clear the text of the sortKeyText element (if any)
                //document.getElementById("sortKeyText").innerHTML = "Available sort key: N/A";
                // Clear the partitionKey value
                partitionKey = ""
            }
            resolve();
        })
    }
    
    // Uses a promise and XMLHttpRequest to request the secondary indexes from a dynamodb table
    function postDescribeTable() {
    // Used to build the contents of the indexList element
    // Building the XMLHttpRequest object to POST to the describetable API endpoint, using sessionStorage.access_token
	    return new Promise(function (resolve, reject) {
            // Make the "Loading" overlay visible
            document.getElementById("loadingOverlay").style.display = "flex";
            document.getElementById("loadingOverlay-content").style.display = "flex";
            
            var describetablepost = new XMLHttpRequest();
            var url = "https://apiid.execute-api.theregion.amazonaws.com/stagename/describetable?queryTerm=" + targetTable;
            describetablepost.open("POST", url, true);
            describetablepost.setRequestHeader("Content-Type", "application/json");
            describetablepost.setRequestHeader("Authorization", sessionStorage.access_token);
    
            describetablepost.onload = function(event){
                const calldbResponse = event.target.response;
                // Remove [] and {} characters from calldbResponse, as well as all empty lines
                calldbResponseClean = calldbResponse.replace(/[\[\]\{\}:]/gm, '');
                //calldbResponseClean2 = calldbResponseClean.replace("Response", '');
                calldbResponseClean2 = calldbResponseClean.replace(/^\\s*$(?:\\r\\n?|\\n)/gm, '');
                // Build lines[] from calldbResponseClean2
                lines = calldbResponseClean2.replace(/\\n/g, "<br>").split("<br>");
                // Create the object to use for appending to the dropdown list element 'indexList' 
                var dropdownItem = document.createElement("option");
                
                // Add the header to the top of indexList
                dropdownItem.innerText = " ---Choose index name--- "
                indexList.appendChild(dropdownItem.cloneNode(true));
                
                // Append the first item in lines[] to the dropdown list element 'indexList'.  This is the primary index and usually lacks the string 'index'.
                try {
                    dropdownItem.innerText = lines[1].replace(/['",]+/g, '');
                
                    // For each line in calldbResponse (skipping lines 1 and 2 because they contains ['KeySchema'] and ['AttributeName'] (the primary key) and should be written on the lines above)
                    for (let n = 0; n < lines.length; n++) {
                        // Check if the line contains 'index'
                        if ( lines[n].includes('index') || n == 1) {
                            // Append that item in lines[] to the dropdown list element 'indexList'
                            dropdownItem.innerText = lines[n].replace(/['",]+/g, '');
                            // cloneNode true is required or only the last element in the array is appended to the indexList element. For
                            //further details see here: https://stackoverflow.com/questions/55354063/appendchild-only-works-on-last-element
                            indexList.appendChild(dropdownItem.cloneNode(true));
                        }
                    }
                } catch (error) {
                    // Hide the "Loading" overlay
                    document.getElementById("loadingOverlay").style.display = "none";
                    document.getElementById("loadingOverlay-content").style.display = "none";
                    console.log(error);
                    // Reload the page to get a new access token
                    document.location.reload();
                    reject(error);
                }
                // Hide the loading overlay
                document.getElementById("loadingOverlay").style.display = "none";
                document.getElementById("loadingOverlay-content").style.display = "none";
                
                resolve();
            };
            // Submit the describetable API POST with the request parameters as queryStrings in the url
            describetablepost.send();
        })
    }

    // Uses a promise and XMLHttpRequest to request all tables in dynamodb
    function postListTables() {
    // Used to build the contents of the tableList element
    // Building the XMLHttpRequest object to POST to the listtables API endpoint, using sessionStorage.access_token
        return new Promise(function (resolve, reject) {
            // Make the "Loading" overlay visible
            document.getElementById("loadingOverlay").style.display = "flex";
            document.getElementById("loadingOverlay-content").style.display = "flex";
            
            let listtablespost = new XMLHttpRequest();
            var url = "https://apiid.execute-api.theregion.amazonaws.com/stagename/listtables";
            listtablespost.open("POST", url, true);
            listtablespost.setRequestHeader("Content-Type", "application/json");
            listtablespost.setRequestHeader("Authorization", sessionStorage.access_token);
    
            listtablespost.onload = function(event){
                const calldbResponse = event.target.response;
                // Remove [] and {} characters from calldbResponse, as well as all empty lines
                calldbResponseClean = calldbResponse.replace(/[\[\]\{\}:]/gm, '');
                //calldbResponseClean2 = calldbResponseClean.replace("Response", '');
                calldbResponseClean2 = calldbResponseClean.replace(/^\\s*$(?:\\r\\n?|\\n)/gm, '');
                // Build linesTable[] from calldbResponseClean2
                linesTable = calldbResponseClean2.replace(/\\n/g, "<br>").split("<br>");
                // Create the object to use for appending to the dropdown list element 'tableList' 
                var dropdownItem = document.createElement("option");
    	        
                // For each line in calldbResponse
                for (let n = 0; n < linesTable.length; n++) {
                    // Don't include the linesTable[n] in the output if it's "response", null, or only spaces
                    if (linesTable[n].toLowerCase().indexOf("response") === -1 && linesTable[n].length > 0 && linesTable[n].trim().length > 0) {
                        // Append that item in linesTable[] to the dropdown list element 'tableList'
                        dropdownItem.innerText = linesTable[n].replace(/['",]+/g, '');
                        // cloneNode true is required or only the last element in the array is appended to the tableList element. For
                        //further details see here: https://stackoverflow.com/questions/55354063/appendchild-only-works-on-last-element
                        // Only append if the table name is outside the blacklist defined above
                        if (!tableBlacklist.includes(dropdownItem.innerText.trim())) {
                            tableList.appendChild(dropdownItem.cloneNode(true));
                        }
                    }
                }
                // Hide the loading overlay
                document.getElementById("loadingOverlay").style.display = "none";
                document.getElementById("loadingOverlay-content").style.display = "none";
                
                resolve();
            };
            // Submit the listtables API POST
            listtablespost.send();
        })
    }

    // Set up page elements based on what's selected from tableList
    function chooseTable() {
    // Set tableName based on what's selected from tableList
    // With the newly updated tableName, use function postDescribeTable to update the indexList
        return new Promise(function (resolve, reject) {    
            //indexName = indexList.options[indexList.selectedIndex].text;
            
            // Set the tableName for the query to the selection from the dropdown list
            tableName = tableList.options[tableList.selectedIndex].text;
            
            document.getElementById("queryInputManual").placeholder="";
            
            // Set up the page elements and partitionKey string based on the selection from the dropdown list
            targetTable = tableName
            
            // After executing this function clear the dropdown contents of the index list
            indexList.textContent = '';
            resolve();
        })
    }

    // Set up page elements based on what's selected from indexList
    function chooseIndex() {
        // If the indexList has no selection then set selectedIndex to the first item
        if ( indexList.selectedIndex == "-1" || indexList.selectedIndex == null ) {
            indexList.selectedIndex = 0;
            //indexList.options[indexList.selectedIndex] = "0";
        }
        // Set the indexName for the query to the selection from the dropdown list
        
        indexName = indexList.options[indexList.selectedIndex].text;
        
        document.getElementById("queryInputManual").placeholder="";
        
        // Set up the page elements and partitionKey string based on the selection from the dropdown list
        // Read in the partitionKey from lines[]
        // For each line
        for (let n = 0; n < lines.length; ) {
            //console.log(lines[n]);
            // Check if the selected indexName is included on the current line
            if ( lines[n].includes(indexName) ) {
            // If true then 
                // iterate the line to the next item
                n++;
                // store that item as the partitionKey
                partitionKey = lines[n].replace(/['",]+/g, '');
                // Iterate the line
                n++;
                // Check if the line includes 'index' (but always trigger on the first line as it is the primary index)
                if ( lines[n].includes('index') || n == 1) {
                // If true then
                    // exit the loop
                    break;
                } else {
                // If false then
                    // store that item as the sortKey
                    sortKey = lines[n].replace(/['",]+/g, '');
                    // exit the loop
                    break;
                }
            } else {
            // If false then 
                // Iterate the line
                n++;
            }
        }
        
        // Set the text of the queryType element
        document.getElementById("queryType").text = 'Query by ' + partitionKey + ':';
        // Set the placeholder text of the queryInputManual element
        document.getElementById("queryInputManual").placeholder = partitionKey;
        // Set the text of the sortKeyText element (if any)
        if ( typeof sortKey != 'undefined' ) {
            //document.getElementById("sortKeyText").innerHTML = "Available sort key: " + sortKey;
        }
    }
    
    // Used in mainFunction() to query dynamoDB
    function callDynamoDB(queryInput, indexName, partitionKey, tableName) {
        return new Promise((resolve, reject) => {
            // If queryInput isn't populated then clear queryResponse and resolve the promise
            //console.log(queryInput);
            if (queryInput.length == 0 || queryInput == null) {
                queryResponse = "";
                reject("Error - A required value for the query was blank");
                // Hide the "Loading" overlay
                document.getElementById("loadingOverlay").style.display = "none";
                document.getElementById("loadingOverlay-content").style.display = "none";
                return;
            }
            // Building the XMLHttpRequest object to POST to the calldb API endpoint, using sessionStorage.access_token
            var apipost = new XMLHttpRequest();
            var url = "https://apiid.execute-api.theregion.amazonaws.com/stagename/calldb?queryTerm="+queryInput+"&indexName="+indexName+"&partitionKey="+partitionKey+"&tableName="+tableName;
            var queryResult;
            apipost.open("POST", url, true);
            apipost.setRequestHeader("Content-Type", "application/json");
            apipost.setRequestHeader("Authorization", sessionStorage.access_token);
            
            // When onreadystatechange is triggered check to confirm that the POST has completed and has returned a 200 response status
            apipost.onreadystatechange = function() {
                if (apipost.readyState === XMLHttpRequest.DONE && apipost.status === 200) {
                    queryResult = apipost.responseText;
                    //console.log("Query result without changes: " + queryResult);
                    queryResultJSON = JSON.parse(queryResult);
                    //console.log("Query result after converting to JSON: ", queryResultJSON);
                    if (queryResultJSON.Items.length === 0) {
                        queryResultJSON.Items = "No values found";
                    }
                    queryResponse = queryResultJSON;
                    resolve();
                } else if (apipost.readyState === XMLHttpRequest.DONE && apipost.status !== 200) {
                    reject("Error - Access token is expired, reload the page.");
                    // Hide the "Loading" overlay
                    document.getElementById("loadingOverlay").style.display = "none";
                    document.getElementById("loadingOverlay-content").style.display = "none";
                    // Reload the page to get a new access token
                    document.location.reload();
                    return;
                }
            };
            // Submit the main API POST with the request parameters as queryStrings in the url
            apipost.send();
        });
    }
    
    // Executes the radio dump, called as defined in the setupClickEvent
    async function mainFunction() {
    	queryAccountnos = [];
	    queryprimaryprofile = [];
	    querysubscriptionid = [];
        
        // Make the "Loading" overlay visible
        document.getElementById("loadingOverlay").style.display = "flex";
        document.getElementById("loadingOverlay-content").style.display = "flex";
        
        /////
        // #1. Query ${DYNAMODB_PREFIX}-device for RadioID/DeviceID (deviceid)
        // Any trailing and leading whitespace around queryInput is removed with trim()
        //console.log("#1. ", queryInput.value.trim());
        try {
            await callDynamoDB(queryInput.value.trim(), "deviceid", "deviceid", "dyntableprefix-device");
            firstQueryJSON = queryResponse;
            for (firstitem of firstQueryJSON.Items) {
                if (firstitem.accountno) {
                    queryAccountnos.push(firstitem.accountno);
                }
                if (firstitem.primaryprofile) {
                    queryprimaryprofile.push(firstitem.primaryprofile);
                }
                if (firstitem.subscriptionid) {
                    querysubscriptionid.push(firstitem.subscriptionid);
                }
            }
            returnValue = document.getElementById("01").innerHTML.concat("\\n------------------------------------------------------------------------------------------------------------------------\\n"
                , "#1. Device ", queryInput.value, " in device:\\n", JSON.stringify(firstQueryJSON.Items, null, 4));
        } catch (error) {
            document.getElementById("01").innerHTML = document.getElementById("01").innerHTML.concat(error);
            console.log(error);
            return;
        }
        // Replace the contents of the "result" element with the apipost.responseText
        // Replace newlines with <br> for HTML formatting
        if (returnValue.includes(\n)) {
            document.getElementById("01").innerHTML = returnValue.replace(/\\n/g, "<br>");
        } else {
            document.getElementById("01").innerHTML = returnValue;
        }
        
        /////
        //#2.  Query table ${DYNAMODB_PREFIX}-aepa for accountno from #1's accountno
        //console.log("#2. ", queryAccountnos);
        document.getElementById("02").innerHTML = document.getElementById("02").innerHTML.concat("\\n------------------------------------------------------------------------------------------------------------------------\\n"
            , "#2. Account ", queryAccountnos, " in aepa:\\n");
        try {
            await callDynamoDB(queryAccountnos, "accountno-index", "accountno", "dyntableprefix-aepa");
        } catch (error) {
            document.getElementById("02").innerHTML = document.getElementById("02").innerHTML.concat(error);
            console.log(error);
            return;
        }
        secondQueryJSON = queryResponse;
        returnValue = document.getElementById("02").innerHTML.concat(JSON.stringify(secondQueryJSON.Items, null, 4));
        // Replace the contents of the "result" element with the apipost.responseText
        // Replace newlines with <br> for HTML formatting
        if (returnValue.includes(\n)) {
            document.getElementById("02").innerHTML = returnValue.replace(/\\n/g, "<br>");
        } else {
            document.getElementById("02").innerHTML = returnValue;
        }
        
        /////
        //#3.  Query table ${DYNAMODB_PREFIX}-listener for accountno from #1's accountno
        document.getElementById("03").innerHTML = document.getElementById("03").innerHTML.concat("\\n------------------------------------------------------------------------------------------------------------------------\\n"
            , "#3. Listeners on account ", queryAccountnos, " in listener:\\n");
        try {
            await callDynamoDB(queryAccountnos, "accountno-index", "accountno", "dyntableprefix-listener");
        } catch (error) {
            document.getElementById("03").innerHTML = document.getElementById("03").innerHTML.concat(error);
            console.log(error);
            return;
        }
        thirdQueryJSON = queryResponse;
        //console.log("#3. ", queryAccountnos);
        queryListenerProfileIds = [];
        for (thirditem of thirdQueryJSON.Items) {
            if (thirditem.profileid) {
                //console.log("profileid: " + thirditem.profileid);
                queryListenerProfileIds.push(thirditem.profileid);
            }
        }
        document.getElementById("03").innerHTML = document.getElementById("03").innerHTML.concat(JSON.stringify(thirdQueryJSON.Items, null, 4));
        
        /////
        //#4.  Query table ${DYNAMODB_PREFIX}-profile for ProfileId from #1's PrimaryProfile
        //console.log("#4. ", queryprimaryprofile[0]);
        document.getElementById("04").innerHTML = document.getElementById("04").innerHTML.concat("\\n------------------------------------------------------------------------------------------------------------------------\\n", 
            "#4. Radio primaryprofile ", queryprimaryprofile[0], " in profile:\\n")
        try {
            await callDynamoDB(queryprimaryprofile[0], "profileid", "profileid", "dyntableprefix-profile");
        } catch (error) {
            document.getElementById("04").innerHTML = document.getElementById("04").innerHTML.concat(error);
            console.log(error);
            return;
        }
        fourthQueryJSON = queryResponse;
        document.getElementById("04").innerHTML = document.getElementById("04").innerHTML.concat(JSON.stringify(fourthQueryJSON.Items, null, 4));
        
        /////
        //#5.  Query table ${DYNAMODB_PREFIX}-profile for all ProfileId from #3's ProfileIds
        //console.log("#5. ", queryListenerProfileIds);
        document.getElementById("05").innerHTML = document.getElementById("05").innerHTML.concat("\\n------------------------------------------------------------------------------------------------------------------------\\n#5. ");
        queryProfileIds = [];
        counter = 0;
        if (queryListenerProfileIds.length > 0) {
            for (listenerprofileid of queryListenerProfileIds) {
                //console.log(listenerprofileid);
                if (counter !== 0) {
                    document.getElementById("05").innerHTML = document.getElementById("05").innerHTML.concat("\\n--------------------\\n#5. ");
                }
                document.getElementById("05").innerHTML = document.getElementById("05").innerHTML.concat("Additional Listeners profileid ", listenerprofileid, " in profile:\\n");
                try {
                    await callDynamoDB(listenerprofileid, "profileid", "profileid", "dyntableprefix-profile");
                } catch (error) {
                    document.getElementById("05").innerHTML = document.getElementById("05").innerHTML.concat(error);
                    console.log(error);
                    return;
                }
                counter = counter + 1;
                fifthQueryJSON = queryResponse;
                //console.log("fifthQueryResponse: " + JSON.stringify(fifthQueryJSON, null, 4));
                for (fifthitem of fifthQueryJSON.Items) {
                    if (fifthitem.profileid) {
                        //console.log("profileid: " + fifthitem.profileid);
                        queryProfileIds.push(fifthitem.profileid);
                    }
                }
                document.getElementById("05").innerHTML = document.getElementById("05").innerHTML.concat(JSON.stringify(fifthQueryJSON.Items, null, 4));
            }
        } else {
            document.getElementById("05").innerHTML = document.getElementById("05").innerHTML.concat("\\nNo ListenerProfileId values to query for.");
        }
        
        /////
        //#6. Query ${DYNAMODB_PREFIX}-subscription for subscriptionid from #1's subscriptionid
        document.getElementById("06").innerHTML = document.getElementById("06").innerHTML.concat("\\n------------------------------------------------------------------------------------------------------------------------\\n"
            , "#6. Radio subscriptionid ", querysubscriptionid[0], " in subscription:\\n");
        try {
            await callDynamoDB(querysubscriptionid[0], "subscriptionid", "subscriptionid", "dyntableprefix-subscription");
        } catch (error) {
            document.getElementById("06").innerHTML = document.getElementById("06").innerHTML.concat(error);
            console.log(error);
            return;
        }
        sixthQueryJSON = queryResponse;
        //console.log("#5.1. ", queryProfileIds);
        //console.log("#6. ", querysubscriptionid[0]);
        queryServiceIds = [];
        returnValue = "";
        for (sixthitem of sixthQueryJSON.Items) {
            if (sixthitem.serviceids) {
                for (sixthserviceid of sixthitem.serviceids) {
                    //console.log("serviceids: " + sixthserviceid);
                    queryServiceIds.push(sixthserviceid);
                }
            }
        }
        document.getElementById("06").innerHTML = document.getElementById("06").innerHTML.concat(JSON.stringify(sixthQueryJSON.Items, null, 4));
        
        /////
        //#7. Loop over every serviceids returned from #6 and query ${DYNAMODB_PREFIX}-service for serviceid
        //console.log("#7. ", queryServiceIds);
        document.getElementById("07").innerHTML = document.getElementById("07").innerHTML.concat("\\n------------------------------------------------------------------------------------------------------------------------\\n#7. ");
        counter = 0;
        if (queryServiceIds.length > 0) {
            for (serviceid of queryServiceIds) {
                if (counter === 0) {
                    document.getElementById("07").innerHTML = document.getElementById("07").innerHTML.concat("Subscription serviceid ", serviceid, " in service:");
                } else {
                    document.getElementById("07").innerHTML = document.getElementById("07").innerHTML.concat("#7. Subscription serviceid ", serviceid, " in service:");
                }
                counter = counter + 1;
                try {
                    await callDynamoDB(serviceid, "serviceid", "serviceid", "dyntableprefix-service");
                } catch (error) {
                    document.getElementById("07").innerHTML = document.getElementById("07").innerHTML.concat(error);
                    console.log(error);
                    return;
                }
                seventhQueryJSON = queryResponse;
                document.getElementById("07").innerHTML = document.getElementById("07").innerHTML.concat("\\n", JSON.stringify(seventhQueryJSON.Items, null, 4), "\\n");
            }
        } else {
            document.getElementById("07").innerHTML = document.getElementById("07").innerHTML.concat("\\nNo ServiceId values to query for.");
        }
        
        /////
        //#8. Query ${DYNAMODB_PREFIX}-account for accountno from #1's accountno
        //console.log("#8. ", queryAccountnos);
        for (accountno of queryAccountnos) {
            document.getElementById("08").innerHTML = document.getElementById("08").innerHTML.concat("\\n------------------------------------------------------------------------------------------------------------------------\\n"
                , "#8. Radio accountno ", accountno, " in account:\\n");
            try {
                await callDynamoDB(accountno, "accountno", "accountno", "dyntableprefix-account");
            } catch (error) {
                document.getElementById("08").innerHTML = document.getElementById("08").innerHTML.concat(error);
                console.log(error);
                return;
            }
            eighthQueryJSON = queryResponse;
            document.getElementById("08").innerHTML = document.getElementById("08").innerHTML.concat(JSON.stringify(eighthQueryJSON.Items, null, 4));
        }
        
        // Hide the loading overlay
        document.getElementById("loadingOverlay").style.display = "none";
        document.getElementById("loadingOverlay-content").style.display = "none";
    }; 

    // Defines the "click" event listener of the submit button
    function setupClickEvent() {

        // Configures submit button page element
        // Executes the query to the calldb API endpoint and populates calldbResponse with the response 
        const submit = document.querySelector('#submit');
        queryInput = document.querySelector('#queryInput');
        tableName = targetTable;
        
        document.getElementById("submit").addEventListener("click", function(){
            // Validate the required inputs
            if ( queryInput.value == '' ) {
                alert("You must enter a value to query for.");
                return;
            }
            
            // Clear the contents of the 'result' div element
            document.getElementById("01").innerHTML = "";
            document.getElementById("02").innerHTML = "";
            document.getElementById("03").innerHTML = "";
            document.getElementById("04").innerHTML = "";
            document.getElementById("05").innerHTML = "";
            document.getElementById("06").innerHTML = "";
            document.getElementById("07").innerHTML = "";
            document.getElementById("08").innerHTML = "";
            
            mainFunction();
        });
    }
    
    // Defines the "click" event listener of the submitManual button
    function executeQuery() {
        return new Promise(function (resolve, reject) {
            // Sets up submit button page element
            // Executes the query to the calldb API endpoint and populates calldbResponse with the response 
            const submit = document.querySelector('#submit');
            const queryInputM = document.querySelector('#queryInputManual');
            tableName = targetTable;
            
            document.getElementById("submitManual").addEventListener("click", function(){
                // Clear the contents of the resultManual element
                document.getElementById("resultManual").innerHTML = "";
                // Validate the required inputs
                if ( typeof partitionKey == 'undefined' ) {
                    alert("You must select an index from the list.");
                    return;
                } else if ( queryInputM.value == '' ) {
                    alert("You must enter a value to query for.");
                    return;
                }
                
                // Make the "Loading" overlay visible
                document.getElementById("loadingOverlay").style.display = "flex";
                document.getElementById("loadingOverlay-content").style.display = "flex";
                    		
                // Building the XMLHttpRequest object to POST to the calldb API endpoint, using sessionStorage.access_token
                var apipost = new XMLHttpRequest();
                // Any leading or trailing whitespace is removed from queryInputM.value with trim()
                var url = "https://apiid.execute-api.theregion.amazonaws.com/stagename/calldb?queryTerm="+queryInputM.value.trim()+"&indexName="+indexName+"&partitionKey="+partitionKey+"&tableName="+tableName;
                apipost.open("POST", url, true);
                apipost.setRequestHeader("Content-Type", "application/json");
                apipost.setRequestHeader("Authorization", sessionStorage.access_token);
                
                apipost.onload = function(event){
                    const calldbResponse = JSON.parse(event.target.response);
                    // Check that calldbResponse.Items is populated
                    if (calldbResponse.Items !== null && calldbResponse.Items !== undefined) {
                        // Print the Items from the API response that queried the DB
                        document.getElementById("resultManual").innerHTML = document.getElementById("resultManual").innerHTML.concat("Response from API call: \\n", JSON.stringify(calldbResponse.Items, null, 4));
                        //document.getElementById("mainAPI Response").innerHTML = "Response from API call: " + calldbResponse.replace(/\\n/g, "<br>");
                        // Hide the loading overlay
                        document.getElementById("loadingOverlay").style.display = "none";
                        document.getElementById("loadingOverlay-content").style.display = "none";
                        resolve();
                    } else {    // Assume calldbResponse is a 401 error and begin the flow to request a new access token
                        // Hide the "Loading" overlay
                        document.getElementById("loadingOverlay").style.display = "none";
                        document.getElementById("loadingOverlay-content").style.display = "none";
                        // Reload the page to get a new access token
                        document.location.reload();
                        reject("Error - Access token is expired, reload the page.");
                    }
                    
                };
                // Ensure that we have a table and index to query
                if ( indexName != 'No secondary indexes found.' ) {
                    // Submit the main API POST with the request parameters as queryStrings in the url
                    apipost.send();
                } else {
                    alert("No secondary indexes found so the query execution has been halted.");
                }
            });
        })
    }
    
    
    //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    // async function used for the initial page load
    async function doMainExecute() {
        await setupClickEvent();                    // Defines the "click" event listener
        await postListTables();                     // Request all tables and build the tableList select element
        try {
            await executeQuery();                       // Defines the "click" event listener
        } catch (error) {
            document.getElementById("resultManual").innerHTML = document.getElementById("resultManual").innerHTML.concat(error);
            console.log(error);
            return;
        }
        // This event is needed to update the size of textareas as they are populated
        let myEvent = new CustomEvent("update");
        textarea.dispatchEvent(myEvent);
        let myEventM = new CustomEvent("updateM");
        textareaM.dispatchEvent(myEventM);
    }
    
    //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////    
    // Check if the page has finished loading before executing doMainExecute()
    if (document.readyState !== 'loading') {
        doMainExecute();
    } else {    
    // If the page is still loading add a listener for the DOMContentLoaded event so that doMainExecute() runs after it loads
        document.addEventListener('DOMContentLoaded', function () {
            doMainExecute();
        });
    }
    

</script>

</body>
</html>"""
    }
    
    # Insert the contents of the environment variables into the response
    thebody = responseToReturn['body']
    thebody = thebody.replace("userpooldomain", userpooldomain)
    thebody = thebody.replace("theregion", theregion)
    thebody = thebody.replace("apiid", apiid)
    thebody = thebody.replace("stagename", stagename)
    thebody = thebody.replace("dyntableprefix", dyntableprefix)
    # Check the scopes passed to the lambda to determine which userpool clientID to use
    if "mainapi/nonce" in theScopes:
        thebody = thebody.replace("userpoolclientid", userpoolclientid2)
    else:
        thebody = thebody.replace("userpoolclientid", userpoolclientid1)

    responseToReturn.update({'body': thebody})
	
    return(responseToReturn)
