// After authenticating with the Cognito App Client the user is redirected to this page, with the authorization code appended to the
//URL as the queryString "code".  This page expects to either have an authorization code in the URL or to have an access_token stored inside
//sessionStorage.
// The javascript executes the following steps in order:
// 1. Use one of two methods to execute executeAuth() after the page has loaded.
// 2. Check the sessionStorage for an access_token
// 3. If there's no access_token then the expectation is that this was just redirected from Cognito with a new auth code in the URL so firstPost() is executed
// 4. If there's an access_token but it's undefined then remove the access_token from sessionStorage and redirect back to the Cognito Hosted UI login page
// 5. If there's an access_token and it's populated then execute reloadPost()

// Function firstPost():
// 1. Read the authorization code from the URL queryString "code" 
// 2. Send a POST to /oauth2/token with the authorization code and store the tokens it responds with in sessionStorage
// 3. Send a POST to the /main API endpoint using the token from sessionStorage 
// 4. Replace the contents of the "mainAPI Response" div element with the response from the POST to /main
// 5. Execute the "executeQuery" script added to the "mainAPI Response" div element

// Function reloadPost():
// 1. Send a POST to the /main API endpoint using the token from sessionStorage 
// 1.a. If /main responds that the access token is expired then use the refresh token in sessionStorage to send a POST to oauth2/token
// 1.a.a. If oauth2/token responds with tokens then store them in sessionStorage and re-run the reloadPost() function 
// 1.a.b. If oauth2/token responds that the refresh token is expired then clear sessionStorage.access_token, then set location.href to redirect back to the Hosted UI login page
// 2. Replace the contents of the "mainAPI Response" div element with the response from the POST to /main
// 3. Execute the "executeQuery" script added to the "mainAPI Response" div element

exports.handler = async (event) => {
	// Read in environment variables to be passed to the js
	var userpooldomain = process.env.userpooldomain;
	var theregion = process.env.theregion;
	var userpoolclientid = process.env.userpoolclientid;
	var apiid = process.env.apiid;
	var stagename = process.env.stagename.toLowerCase();
    const response = {
        statusCode: 200,
        headers: {
            "Content-Type": "text/html"
        },
        body: `<!DOCTYPE html>
<html>

<!-- This line prevents 403 errors for the favicon.ico when loading the page -->
<link rel="icon" href="data:;base64,iVBORw0KGgo=">

<!-- Create element to be replaced by the response -->
<div id="mainAPI Response" style="whitespace:pre"></div>

<script type="text/javascript">
    
    function firstPost(url) {
        // Use Proxy() and URLSearchParams(window.location.search) to locate the value of the queryString in the URL named 'code'
        const params = new Proxy(new URLSearchParams(window.location.search), { 
            get: (searchParams, prop) => searchParams.get(prop), }
        );
        let codevalue = params.code;
        
        // Building the XMLHttpRequest object to POST to oauth2/token
        var authpost = new XMLHttpRequest();
        var url = "https://userpooldomain.auth.theregion.amazoncognito.com/oauth2/token";
        authpost.open("POST", url, true);
        authpost.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
        authpost.onload = function(event){
            const authResponse = event.target.response;
            const authResponseJSON = JSON.parse(authResponse);
            // Store the access and refresh tokens in session storage
            sessionStorage.setItem("access_token", authResponseJSON.access_token);
            sessionStorage.setItem("refresh_token", authResponseJSON.refresh_token);
            
            // Building the XMLHttpRequest object to POST to the main API endpoint, using sessionStorage.access_token
            var apipost = new XMLHttpRequest();
            var url = "https://apiid.execute-api.theregion.amazonaws.com/stagename/main";
            apipost.open("POST", url, true);
            apipost.setRequestHeader("Content-Type", "application/json");
            apipost.setRequestHeader("Authorization", sessionStorage.access_token);
            apipost.onload = function(event){
                const mainapiResponse = event.target.response;
                // Replace the contents of the "mainAPI Response" div element with the response from the POST to /main
                //document.getElementById("mainAPI Response").innerHTML = "Response from API call: " + mainapiResponse;
                document.getElementById("mainAPI Response").innerHTML = mainapiResponse;
                // Use eval to execute the code within the mainapiResponse
                // This is done to build the submission forms for the dynamoDB queries, as defined by the main API endpoint
                eval(document.getElementById("executeQuery").innerHTML);
            };
            
            // Submit the POST to /main with the sessionStorage.access_token (generated during authpost.onload) 
            apipost.send();
        };
        
        // Submit the authorization_code grant POST to oauth2/token with the request parameters as queryStrings in the URL
        authpost.send('grant_type=authorization_code&client_id=userpoolclientid&code='+codevalue+'&scope=aws.cognito.signin.user.admin+openid+email+mainapi/api+phone&redirect_uri=https://apiid.execute-api.theregion.amazonaws.com/stagename/redirect');
    }
    
    function reloadPost() {
        // Building the XMLHttpRequest object to POST to the main API endpoint, using sessionStorage.access_token
        var apipost = new XMLHttpRequest();
        var url = "https://apiid.execute-api.theregion.amazonaws.com/stagename/main";
        apipost.open("POST", url, true);
        apipost.setRequestHeader("Content-Type", "application/json");
        apipost.setRequestHeader("Authorization", sessionStorage.access_token);
        apipost.onload = function(event){
            const mainapiResponse = event.target.response;
            /// Check if mainapiResponse is returning an expired token message
            if (mainapiResponse.includes("The incoming token has expired")) {
                // Check if refresh_token exists
                if (sessionStorage.refresh_token) {
                    // Building the XMLHttpRequest object to POST to oauth2/token
                    var refreshpost = new XMLHttpRequest();
                    var url = "https://userpooldomain.auth.theregion.amazoncognito.com/oauth2/token";
                    refreshpost.open("POST", url, true);
                    refreshpost.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
                    refreshpost.onload = function(event){
                        const refreshResponse = event.target.response;
                        // Check if refreshResponse returned an invalid grant message
                        if (refreshResponse.includes("invalid_grant")) {
                            // Clear the contents of sessionStorage.access_token so firstPost() is executed after login,
                            // then redirect to the hosted UI login page and exit
                            sessionStorage.removeItem("access_token");
                            location.href = "https://userpooldomain.auth.theregion.amazoncognito.com/oauth2/authorize?client_id=userpoolclientid&response_type=code&scope=aws.cognito.signin.user.admin+email+mainapi%2Fapi+openid+phone&redirect_uri=https%3A%2F%2Fapiid.execute-api.theregion.amazonaws.com%2Ftest%2Fredirect";
                            return;
                        }
                        // Store the new access token in the session storage
                        sessionStorage.setItem("access_token", JSON.parse(refreshResponse).access_token);
                        // Now that we have the new access token rerun reloadPost()
                        reloadPost();
                        return;
                    };
                    // Submit the refresh_token grant POST to oauth2/token with the request parameters as queryStrings in the URL
                    refreshpost.send('grant_type=refresh_token&client_id=userpoolclientid&refresh_token='+sessionStorage.refresh_token+'&scope=aws.cognito.signin.user.admin+openid+email+mainapi/api+phone&redirect_uri=https://apiid.execute-api.theregion.amazonaws.com/stagename/redirect');
                }
            }
            // Replace the contents of the "mainAPI Response" div element with the response from the POST to /main 
            //document.getElementById("mainAPI Response").innerHTML = "Response from API call: " + mainapiResponse;
            document.getElementById("mainAPI Response").innerHTML = mainapiResponse;
            
            
            // Check if the executeQuery element exists (it doesn't during the refresh_token flow)
            if (document.getElementById("executeQuery") !== undefined && document.getElementById("executeQuery") !== null) {
                // Use eval to execute the code within the mainapiResponse
                // This is done to build the submission forms for the dynamoDB queries, as defined by the main API endpoint
                eval(document.getElementById("executeQuery").innerHTML);
            }
        };
        
        // Submit the POST to /main with the sessionStorage.access_token
        apipost.send();
    }
    
    function executeAuth() {
        // This is done using two separate functions because the XMLHttpRequests have to be nested using IIFEs and
        //the authorization_code grant flow is only needed on the first page load
        // Check the sessionStorage for the access token to see if this is a new session
        if ( ! sessionStorage.access_token ) {
            // If there's no sessionStorage.access_token then we expect the authorization 'code' in the queryString
            firstPost("https://userpooldomain.auth.theregion.amazoncognito.com/oauth2/token");
        // Check for a null access token, this can happen when the browser first starts and relaunches any saved tabs
        } else if ( sessionStorage.access_token === 'undefined' ) {
            // Clear the empty access token from session storage
            sessionStorage.removeItem("access_token");
            // Redirect back to the login page to aquire a new auth code
            location.href = "https://userpooldomain.auth.theregion.amazoncognito.com/oauth2/authorize?client_id=userpoolclientid&response_type=code&scope=aws.cognito.signin.user.admin+email+mainapi%2Fapi+openid+phone&redirect_uri=https%3A%2F%2Fapiid.execute-api.theregion.amazonaws.com%2Ftest%2Fredirect";
            return;
        // If sessionStorage.access_token is populated then we can assume the authorization code to have been used so 
        //the authentication flow is different
        } else {
            reloadPost();
        }
    }
    
    // Check if the page has finished loading before executing executeAuth()
    if (document.readyState !== 'loading') {
        executeAuth();
        // If the page is still loading add a listener for the DOMContentLoaded event so that executeAuth() runs after it loads
    } else {
        document.addEventListener('DOMContentLoaded', function () {
            executeAuth();
        });
    }
    

</script>

</html>`
    };
    // Replace variables within the response body
	response.body = response.body.replace(/userpooldomain/g, userpooldomain);
	response.body = response.body.replace(/theregion/g, theregion);
	response.body = response.body.replace(/userpoolclientid/g, userpoolclientid);
	response.body = response.body.replace(/apiid/g, apiid);
	response.body = response.body.replace(/stagename/g, stagename);
    return response;
};
