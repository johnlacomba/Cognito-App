terraform {
    backend "s3" {}
    required_providers {
        aws = {
        source  = "hashicorp/aws"
        }
    }
}

provider "aws" {
    region = var.region
    default_tags {
        tags = {
            "environment-type" = lower(var.var_env)
        }
    }
}

locals {
  MetadataURLsOnelogin = {
    SIT = ""
    DEV = ""
    PERF = ""
    PROD = ""
  }
}

locals {
  MetadataURLsOnelogin2 = {
    SIT = ""
    DEV = ""
    PERF = ""
    PROD = ""
  }
}

locals {
  MetadataURLsOkta = {
    SIT = ""
    DEV = ""
    PERF = ""
    PROD = ""
  }
}

locals {
  MetadataURLsOkta2 = {
    SIT = ""
    DEV = ""
    PERF = ""
    PROD = ""
  }
}

locals {
  AccountInfoAWS = {
    SIT = "AwsAccountNumber"
    DEV = ""
    PERF = ""
    PROD = ""
  }
}

############## IAM Role ##############
resource "aws_iam_role" "TheApp_role" {

  name = "TheApp_${lower(var.var_env)}"

  assume_role_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF
  tags = {
    Description: "Role used by TheApp"
  }
}

############## IAM Policy ##############
resource "aws_iam_policy" "TheApp_policy" {
    name = "TheAppCmkKms_${lower(var.var_env)}"

    policy = <<EOF
{
    "Statement": [
        {
            "Action": [
                "kms:Decrypt",
                "kms:Encrypt",
                "kms:GenerateDataKey"
            ],
            "Effect": "Allow",
            "Resource": [
                "arn:aws:kms:*:${var.account_id}:key/*"
            ],
            "Sid": "VisualEditor0"
        }
    ],
    "Version": "2012-10-17"
}
EOF
}

resource "aws_iam_policy" "TheApp_lambdapolicy" {
    name = "TheAppLambdaBucket_${lower(var.var_env)}"

    policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListObject",
                "s3:GetObject",
                "s3:PutObject",
                "s3:PutObjectAcl"
            ],
            "Resource": "arn:aws:s3:::theapp-lambdas/*"

        }
    ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "TheAppCmkKms" {
  role = aws_iam_role.TheApp_role.name
  policy_arn = aws_iam_policy.TheApp_policy.arn
}

resource "aws_iam_role_policy_attachment" "AmazonDynamoDBFullAccess" {
  role = aws_iam_role.TheApp_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

# For cloudwatch permissions
resource "aws_iam_role_policy_attachment" "AWSLambdaBasicExecutionRole" {
  role = aws_iam_role.TheApp_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# For the S3 bucket where the Lambda zips are
resource "aws_iam_role_policy_attachment" "TheApp_lambdapolicy" {
  role = aws_iam_role.TheApp_role.name
  policy_arn = aws_iam_policy.TheApp_lambdapolicy.arn
}

############## user pool ##############
resource "aws_cognito_user_pool" "theapp-lambda-SAML" {
  name = "theapp-lambda-SAML-${lower(var.var_env)}"
  admin_create_user_config {
  allow_admin_create_user_only = true
  }
}

############## user pool domain ##############
resource "aws_cognito_user_pool_domain" "theapp" {
  domain       = "theapp-${lower(var.var_env)}"
  user_pool_id = aws_cognito_user_pool.theapp-lambda-SAML.id
}

############## identity providers ##############
resource "aws_cognito_identity_provider" "Onelogin" {
  user_pool_id  = aws_cognito_user_pool.theapp-lambda-SAML.id
  provider_name = "Onelogin"
  provider_type = "SAML"

  provider_details = {
    MetadataURL      = local.MetadataURLsOnelogin[var.var_env]
#    client_id        = aws_cognito_user_pool_client.theapp-lambda-SAML-client-noSecret.id
  }

  attribute_mapping = {
    email    = "NAMEID"
  }
}

resource "aws_cognito_identity_provider" "Onelogin2" {
  user_pool_id  = aws_cognito_user_pool.theapp-lambda-SAML.id
  provider_name = "Onelogin2"
  provider_type = "SAML"

  provider_details = {
    MetadataURL      = local.MetadataURLsOnelogin2[var.var_env]
#    client_id        = aws_cognito_user_pool_client.theapp-lambda-SAML-client-noSecret.id
  }

  attribute_mapping = {
    email    = "NAMEID"
  }
}

resource "aws_cognito_identity_provider" "Okta" {
  user_pool_id  = aws_cognito_user_pool.theapp-lambda-SAML.id
  provider_name = "Okta"
  provider_type = "SAML"

  provider_details = {
    MetadataURL      = local.MetadataURLsOkta[var.var_env]
#    client_id        = aws_cognito_user_pool_client.theapp-lambda-SAML-client-noSecret.id
  }

  attribute_mapping = {
    email    = "NAMEID"
  }
}

resource "aws_cognito_identity_provider" "Okta2" {
  user_pool_id  = aws_cognito_user_pool.theapp-lambda-SAML.id
  provider_name = "Okta2"
  provider_type = "SAML"

  provider_details = {
    MetadataURL      = local.MetadataURLsOkta2[var.var_env]
#    client_id        = aws_cognito_user_pool_client.theapp-lambda-SAML-client-noSecret.id
  }

  attribute_mapping = {
    email    = "NAMEID"
  }
}

############## mainapi resource server and scope ##############
resource "aws_cognito_resource_server" "mainapi" {
  identifier = "mainapi"
  name       = "API"

  scope {
    scope_name        = "api"
    scope_description = "The main api scope"
  }

  scope {
    scope_name        = "nonce"
    scope_description = "For accessing nonce keys"
  }

  user_pool_id = aws_cognito_user_pool.theapp-lambda-SAML.id
}

############## Main App Client ##############
resource "aws_cognito_user_pool_client" "theapp-lambda-SAML-client-noSecret" {
  name = "theapp-lambda-SAML-client-noSecret-${lower(var.var_env)}"

  user_pool_id = aws_cognito_user_pool.theapp-lambda-SAML.id

  generate_secret                      = false
  explicit_auth_flows                  = ["ALLOW_CUSTOM_AUTH","ALLOW_REFRESH_TOKEN_AUTH","ALLOW_USER_SRP_AUTH"]
  callback_urls                        = ["https://${aws_api_gateway_rest_api.theapp-cognito.id}.execute-api.${var.region}.amazonaws.com/${lower(var.var_env)}/redirect"]
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["phone", "email", "openid", "aws.cognito.signin.user.admin", "mainapi/api"]
  supported_identity_providers         = ["Onelogin", "Okta"]
  refresh_token_validity               = 1
  access_token_validity                = 60
  id_token_validity                    = 60
  token_validity_units                 {
                                         refresh_token = "days"
                                         access_token = "minutes"
                                         id_token = "minutes"
                                       }
  depends_on = [
    aws_cognito_identity_provider.Onelogin,
    aws_cognito_identity_provider.Okta
  ]
}

############## Nonce App Client ##############
resource "aws_cognito_user_pool_client" "theapp-lambda-SAML-client-noSecret-allowNonce" {
  name = "theapp-lambda-SAML-client-noSecret-allowNonce-${lower(var.var_env)}"

  user_pool_id = aws_cognito_user_pool.theapp-lambda-SAML.id

  generate_secret                      = false
  explicit_auth_flows                  = ["ALLOW_CUSTOM_AUTH","ALLOW_REFRESH_TOKEN_AUTH","ALLOW_USER_SRP_AUTH"]
  callback_urls                        = ["https://${aws_api_gateway_rest_api.theapp-cognito.id}.execute-api.${var.region}.amazonaws.com/${lower(var.var_env)}/redirect2"]
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["phone", "email", "openid", "aws.cognito.signin.user.admin", "mainapi/api", "mainapi/nonce"]
  supported_identity_providers         = ["Onelogin2", "Okta2"]
  refresh_token_validity               = 1
  access_token_validity                = 60
  id_token_validity                    = 60
  token_validity_units                 {
                                         refresh_token = "days"
                                         access_token = "minutes"
                                         id_token = "minutes"
                                       }
  depends_on = [
    aws_cognito_identity_provider.Onelogin2,
    aws_cognito_identity_provider.Okta2
  ]
}

############## Lambda functions ##############
resource "aws_lambda_function" "theapp-redirect" {
  # If the file is not in the current working directory you will need to include a path.module in the filename.
  s3_bucket = "theapp-lambdas"
  s3_key    = "theapp-redirect-${var.var_redirect_version}.zip"
  function_name = "theapp-redirect-${lower(var.var_env)}"
  handler = "index.handler"
  role          = aws_iam_role.TheApp_role.arn
  runtime = "nodejs22.x"
  environment {
    variables = {
      userpooldomain = aws_cognito_user_pool_domain.theapp.domain
      theregion = var.region
      userpoolclientid = aws_cognito_user_pool_client.theapp-lambda-SAML-client-noSecret.id
      apiid = aws_api_gateway_rest_api.theapp-cognito.id
      stagename = lower(var.var_env)
    }
  }
}

resource "aws_lambda_function" "theapp-redirect2" {
  # If the file is not in the current working directory you will need to include a path.module in the filename.
  s3_bucket = "theapp-lambdas"
  s3_key    = "theapp-redirect2-${var.var_redirect2_version}.zip"
  function_name = "theapp-redirect2-${lower(var.var_env)}"
  handler = "index.handler"
  role          = aws_iam_role.TheApp_role.arn
  runtime = "nodejs22.x"
  environment {
    variables = {
      userpooldomain = aws_cognito_user_pool_domain.theapp.domain
      theregion = var.region
      userpoolclientid = aws_cognito_user_pool_client.theapp-lambda-SAML-client-noSecret-allowNonce.id
      apiid = aws_api_gateway_rest_api.theapp-cognito.id
      stagename = lower(var.var_env)
    }
  }
}

resource "aws_lambda_function" "theapp-dynamodb" {
  s3_bucket = "theapp-lambdas"
  s3_key      = "theapp-dynamodb-${var.var_dynamodb_version}.zip"
  function_name = "theapp-dynamodb-${lower(var.var_env)}"
  handler = "lambda_function.lambda_handler"
  role          = aws_iam_role.TheApp_role.arn
  runtime = "python3.9"
}

resource "aws_lambda_function" "theapp-dynamodbDescribeTable" {
  s3_bucket = "theapp-lambdas"
  s3_key      = "theapp-dynamodbDescribeTable-${var.var_dynamodbDescribeTable_version}.zip"
  function_name = "theapp-dynamodbDescribeTable-${lower(var.var_env)}"
  handler = "lambda_function.lambda_handler"
  role          = aws_iam_role.TheApp_role.arn
  runtime = "python3.9"
}

resource "aws_lambda_function" "theapp-ListTables" {
  s3_bucket = "theapp-lambdas"
  s3_key      = "theapp-listTables-${var.var_ListTables_version}.zip"
  function_name = "theapp-ListTables-${lower(var.var_env)}"
  handler = "lambda_function.lambda_handler"
  role          = aws_iam_role.TheApp_role.arn
  runtime = "python3.9"
  environment {
    variables = {
      userpooldomain = aws_cognito_user_pool_domain.theapp.domain
      theregion = var.region
      userpoolclientid = aws_cognito_user_pool_client.theapp-lambda-SAML-client-noSecret.id
      apiid = aws_api_gateway_rest_api.theapp-cognito.id
      stagename = lower(var.var_env)
    }
  }
}

resource "aws_lambda_function" "theapp-main" {
  s3_bucket = "theapp-lambdas"
  s3_key      = "theapp-main-${var.var_main_version}.zip"
  function_name = "theapp-main-${lower(var.var_env)}"
  handler = "lambda_function.lambda_handler"
  role          = aws_iam_role.TheApp_role.arn
  runtime = "python3.9"
  environment {
    variables = {
      userpooldomain = aws_cognito_user_pool_domain.theapp.domain
      theregion = var.region
      userpoolclientid1 = aws_cognito_user_pool_client.theapp-lambda-SAML-client-noSecret.id
      userpoolclientid2 = aws_cognito_user_pool_client.theapp-lambda-SAML-client-noSecret-allowNonce.id
      apiid = aws_api_gateway_rest_api.theapp-cognito.id
      stagename = lower(var.var_env)
    }
  }
}

############## Metric Filters ##############
resource "aws_cloudwatch_log_metric_filter" "theapp-dynamodb_invocations_metric_filter" {
  name           = "theapp-dynamodb-${lower(var.var_env)}_invocations"
  pattern        = "[FilterForLinesStartingWithUsername = \"Username\", , , , Username, , , , LogIndex, , , , PartitionKey, , , Table]"
  log_group_name = "/aws/lambda/theapp-dynamodb-${lower(var.var_env)}"

  metric_transformation {
    name      = "Queries_using_theapp-dynamodb-${lower(var.var_env)}"
    namespace = "Lambda/theapp"
    value     = "1"
    unit      = "Count"
    dimensions = {
    "By-Username" = "$Username"
    }
  }
  depends_on = [
    aws_lambda_function.theapp-dynamodb
  ]
}

############## SNS Topic ##############
resource "aws_sns_topic" "theapp-topic" {
  name = "theapp-${lower(var.var_env)}"
}

############## SNS Subscriptions ##############
resource "aws_sns_topic_subscription" "email-target" {
  topic_arn = aws_sns_topic.theapp-topic.arn
  protocol  = "email"
  endpoint  = "alertNotifications@example.com"
  depends_on = [
    aws_sns_topic.theapp-topic
  ]
}

############## Metric Filter Alarms ##############
resource "aws_cloudwatch_metric_alarm" "theapp-dynamodb_invocations_metric_filter_alarm" {
  alarm_name                = "Invoke alarm for theapp-dynamodb-${lower(var.var_env)}"
  comparison_operator       = "GreaterThanThreshold"
  evaluation_periods        = 1
  threshold                 = 20
  alarm_description         = "The Lambda \"theapp-dynamodb-${lower(var.var_env)}\" in ${local.AccountInfoAWS[var.var_env]} has been invoked more then 20 times in the last three hours by a single user.  https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2?graph=~(metrics~(~(~(expression~'SELECT*20COUNT*28*22Queries_using_theapp-dynamodb-${lower(var.var_env)}*22*29*20FROM*20*22Lambda*2ftheapp*22*20GROUP*20BY*20*22By-Username*22~id~'q1~period~60~stat~'Sum~yAxis~'left)))~view~'timeSeries~stacked~false~region~'us-east-1~stat~'Sum~period~60)&query=~'7bLambda2ftheapp2cBy-Username7d*20Queries_using_theapp-dynamodb-${lower(var.var_env)}"
  alarm_actions             = [aws_sns_topic.theapp-topic.arn]
  metric_query {
    id          = "toreturn"
    expression  = "MAX(q1)"
    label       = "Max(By-Username) invocations of theapp-dynamodb-${lower(var.var_env)}"
    return_data = "true"
  }
  metric_query {
    id          = "q1"
    expression  = "SELECT COUNT(\"Queries_using_theapp-dynamodb-${lower(var.var_env)}\") FROM \"Lambda/theapp\" GROUP BY \"By-Username\""
    period      = 10800
  }
  depends_on = [
    aws_cloudwatch_log_metric_filter.theapp-dynamodb_invocations_metric_filter,
    aws_sns_topic_subscription.email-target,
    aws_sns_topic.theapp-topic
  ]
}

############## API Authorizer ##############
resource "aws_api_gateway_authorizer" "theapp-cognito-authorizer" {
  name                   = "theapp-cognito-authorizer"
  type                   = "COGNITO_USER_POOLS"
  rest_api_id            = aws_api_gateway_rest_api.theapp-cognito.id
  provider_arns          = [aws_cognito_user_pool.theapp-lambda-SAML.arn]
  authorizer_credentials = aws_iam_role.TheApp_role.arn
}

############## Rest API ##############
resource "aws_api_gateway_rest_api" "theapp-cognito" {
  name = "theapp-cognito-${lower(var.var_env)}"
  put_rest_api_mode = "merge"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

############## Rest API endpoints ##############
resource "aws_api_gateway_resource" "theapp-redirect" {
  parent_id   = aws_api_gateway_rest_api.theapp-cognito.root_resource_id
  path_part   = "redirect"
  rest_api_id = aws_api_gateway_rest_api.theapp-cognito.id
}

resource "aws_api_gateway_resource" "theapp-redirect2" {
  parent_id   = aws_api_gateway_rest_api.theapp-cognito.root_resource_id
  path_part   = "redirect2"
  rest_api_id = aws_api_gateway_rest_api.theapp-cognito.id
}

resource "aws_api_gateway_resource" "theapp-main" {
  parent_id   = aws_api_gateway_rest_api.theapp-cognito.root_resource_id
  path_part   = "main"
  rest_api_id = aws_api_gateway_rest_api.theapp-cognito.id
}

resource "aws_api_gateway_resource" "theapp-describetable" {
  parent_id   = aws_api_gateway_rest_api.theapp-cognito.root_resource_id
  path_part   = "describetable"
  rest_api_id = aws_api_gateway_rest_api.theapp-cognito.id
}

resource "aws_api_gateway_resource" "theapp-listtables" {
  parent_id   = aws_api_gateway_rest_api.theapp-cognito.root_resource_id
  path_part   = "listtables"
  rest_api_id = aws_api_gateway_rest_api.theapp-cognito.id
}

resource "aws_api_gateway_resource" "theapp-calldb" {
  parent_id   = aws_api_gateway_rest_api.theapp-cognito.root_resource_id
  path_part   = "calldb"
  rest_api_id = aws_api_gateway_rest_api.theapp-cognito.id
}

############## Rest API methods ##############
resource "aws_api_gateway_method" "theapp-redirectget" {
  authorization = "NONE"
  http_method   = "GET"
  resource_id   = aws_api_gateway_resource.theapp-redirect.id
  rest_api_id   = aws_api_gateway_rest_api.theapp-cognito.id
}

resource "aws_api_gateway_method" "theapp-redirect2get" {
  authorization = "NONE"
  http_method   = "GET"
  resource_id   = aws_api_gateway_resource.theapp-redirect2.id
  rest_api_id   = aws_api_gateway_rest_api.theapp-cognito.id
}

resource "aws_api_gateway_method" "theapp-mainpost" {
  authorization = "COGNITO_USER_POOLS"
  authorization_scopes = ["phone", "email", "openid", "aws.cognito.signin.user.admin", "mainapi/api"]
  http_method   = "POST"
  resource_id   = aws_api_gateway_resource.theapp-main.id
  rest_api_id   = aws_api_gateway_rest_api.theapp-cognito.id
  authorizer_id = aws_api_gateway_authorizer.theapp-cognito-authorizer.id
  request_parameters   = {
    "method.request.querystring.indexName"       = false
    "method.request.querystring.partitionKey" = false
    "method.request.querystring.queryTerm"       = false
    "method.request.querystring.tableName"       = false
  }
}

resource "aws_api_gateway_method" "theapp-describetablepost" {
  authorization = "COGNITO_USER_POOLS"
  authorization_scopes = ["phone", "email", "openid", "aws.cognito.signin.user.admin", "mainapi/api"]
  http_method   = "POST"
  resource_id   = aws_api_gateway_resource.theapp-describetable.id
  rest_api_id   = aws_api_gateway_rest_api.theapp-cognito.id
  authorizer_id = aws_api_gateway_authorizer.theapp-cognito-authorizer.id
  request_parameters   = {
    "method.request.querystring.indexName"       = false
    "method.request.querystring.partitionKey" = false
    "method.request.querystring.queryTerm"       = false
    "method.request.querystring.tableName"       = false
  }
}

resource "aws_api_gateway_method" "theapp-listtablespost" {
  authorization = "COGNITO_USER_POOLS"
  authorization_scopes = ["phone", "email", "openid", "aws.cognito.signin.user.admin", "mainapi/api"]
  http_method   = "POST"
  resource_id   = aws_api_gateway_resource.theapp-listtables.id
  rest_api_id   = aws_api_gateway_rest_api.theapp-cognito.id
  authorizer_id = aws_api_gateway_authorizer.theapp-cognito-authorizer.id
  request_parameters   = {
    "method.request.querystring.queryTerm"       = false
  }
}

resource "aws_api_gateway_method" "theapp-calldbpost" {
  authorization = "COGNITO_USER_POOLS"
  authorization_scopes = ["phone", "email", "openid", "aws.cognito.signin.user.admin", "mainapi/api"]
  http_method   = "POST"
  resource_id   = aws_api_gateway_resource.theapp-calldb.id
  rest_api_id   = aws_api_gateway_rest_api.theapp-cognito.id
  authorizer_id = aws_api_gateway_authorizer.theapp-cognito-authorizer.id
  request_parameters   = {
    "method.request.querystring.indexName"       = false
    "method.request.querystring.partitionKey" = false
    "method.request.querystring.queryTerm"       = false
    "method.request.querystring.tableName"       = false
  }
}

############## Rest API integrations  ##############
resource "aws_api_gateway_integration" "theapp-redirectintegration" {
  http_method = aws_api_gateway_method.theapp-redirectget.http_method
  resource_id = aws_api_gateway_resource.theapp-redirect.id
  rest_api_id = aws_api_gateway_rest_api.theapp-cognito.id
  timeout_milliseconds = 6000
  integration_http_method = "POST"
  type        = "AWS_PROXY"
  uri = aws_lambda_function.theapp-redirect.invoke_arn
  depends_on = [
    aws_api_gateway_method.theapp-redirectget
  ]
}

resource "aws_api_gateway_integration" "theapp-redirect2integration" {
  http_method = aws_api_gateway_method.theapp-redirect2get.http_method
  resource_id = aws_api_gateway_resource.theapp-redirect2.id
  rest_api_id = aws_api_gateway_rest_api.theapp-cognito.id
  timeout_milliseconds = 6000
  integration_http_method = "POST"
  type        = "AWS_PROXY"
  uri = aws_lambda_function.theapp-redirect2.invoke_arn
  depends_on = [
    aws_api_gateway_method.theapp-redirect2get
  ]
}

resource "aws_api_gateway_integration" "theapp-mainintegration" {
  http_method = aws_api_gateway_method.theapp-mainpost.http_method
  resource_id = aws_api_gateway_resource.theapp-main.id
  rest_api_id = aws_api_gateway_rest_api.theapp-cognito.id
  timeout_milliseconds = 6000
  integration_http_method = "POST"
  type        = "AWS_PROXY"
  uri = aws_lambda_function.theapp-main.invoke_arn
  depends_on = [
    aws_api_gateway_method.theapp-mainpost
  ]
}

resource "aws_api_gateway_integration" "theapp-describetableintegration" {
  http_method = aws_api_gateway_method.theapp-describetablepost.http_method
  resource_id = aws_api_gateway_resource.theapp-describetable.id
  rest_api_id = aws_api_gateway_rest_api.theapp-cognito.id
  timeout_milliseconds = 6000
  integration_http_method = "POST"
  type        = "AWS_PROXY"
  uri = aws_lambda_function.theapp-dynamodbDescribeTable.invoke_arn
  depends_on = [
    aws_api_gateway_method.theapp-describetablepost
  ]
}

resource "aws_api_gateway_integration" "theapp-listtablesintegration" {
  http_method = aws_api_gateway_method.theapp-listtablespost.http_method
  resource_id = aws_api_gateway_resource.theapp-listtables.id
  rest_api_id = aws_api_gateway_rest_api.theapp-cognito.id
  timeout_milliseconds = 6000
  integration_http_method = "POST"
  type        = "AWS_PROXY"
  uri = aws_lambda_function.theapp-ListTables.invoke_arn
  depends_on = [
    aws_api_gateway_method.theapp-listtablespost
  ]
}

resource "aws_api_gateway_integration" "theapp-calldbintegration" {
  http_method = aws_api_gateway_method.theapp-calldbpost.http_method
  resource_id = aws_api_gateway_resource.theapp-calldb.id
  rest_api_id = aws_api_gateway_rest_api.theapp-cognito.id
  timeout_milliseconds = 6000
  integration_http_method = "POST"
  type        = "AWS_PROXY"
  uri = aws_lambda_function.theapp-dynamodb.invoke_arn
  depends_on = [
    aws_api_gateway_method.theapp-calldbpost
  ]
}

############## Rest API integration responses  ##############
resource "aws_api_gateway_integration_response" "theapp-redirect-integrationresponse" {
  rest_api_id = aws_api_gateway_rest_api.theapp-cognito.id
  resource_id = aws_api_gateway_resource.theapp-redirect.id
  http_method = aws_api_gateway_method.theapp-redirectget.http_method
  status_code = "200"

  # Transforms the backend JSON response to XML
  response_templates = {
    "application/xml" = <<EOF
#set($inputRoot = $input.path('$'))
<?xml version="1.0" encoding="UTF-8"?>
<message>
    $inputRoot.body
</message>
EOF
  }
  depends_on = [
    aws_api_gateway_integration.theapp-redirectintegration
  ]
}

resource "aws_api_gateway_integration_response" "theapp-redirect2-integrationresponse" {
  rest_api_id = aws_api_gateway_rest_api.theapp-cognito.id
  resource_id = aws_api_gateway_resource.theapp-redirect2.id
  http_method = aws_api_gateway_method.theapp-redirect2get.http_method
  status_code = "200"

  # Transforms the backend JSON response to XML
  response_templates = {
    "application/xml" = <<EOF
#set($inputRoot = $input.path('$'))
<?xml version="1.0" encoding="UTF-8"?>
<message>
    $inputRoot.body
</message>
EOF
  }
  depends_on = [
    aws_api_gateway_integration.theapp-redirect2integration
  ]
}

resource "aws_api_gateway_integration_response" "theapp-main-integrationresponse" {
  rest_api_id = aws_api_gateway_rest_api.theapp-cognito.id
  resource_id = aws_api_gateway_resource.theapp-main.id
  http_method = aws_api_gateway_method.theapp-mainpost.http_method
  status_code = "200"

  # Transforms the backend JSON response to XML
  response_templates = {
    "application/xml" = <<EOF
#set($inputRoot = $input.path('$'))
<?xml version="1.0" encoding="UTF-8"?>
<message>
    $inputRoot.body
</message>
EOF
  }
  depends_on = [
    aws_api_gateway_integration.theapp-mainintegration
  ]
}

resource "aws_api_gateway_integration_response" "theapp-describetable-integrationresponse" {
  rest_api_id = aws_api_gateway_rest_api.theapp-cognito.id
  resource_id = aws_api_gateway_resource.theapp-describetable.id
  http_method = aws_api_gateway_method.theapp-describetablepost.http_method
  status_code = "200"

  # Transforms the backend JSON response to XML
  response_templates = {
    "application/xml" = <<EOF
#set($inputRoot = $input.path('$'))
<?xml version="1.0" encoding="UTF-8"?>
<message>
    $inputRoot.body
</message>
EOF
  }
  depends_on = [
    aws_api_gateway_integration.theapp-describetableintegration
  ]
}

resource "aws_api_gateway_integration_response" "theapp-listtables-integrationresponse" {
  rest_api_id = aws_api_gateway_rest_api.theapp-cognito.id
  resource_id = aws_api_gateway_resource.theapp-listtables.id
  http_method = aws_api_gateway_method.theapp-listtablespost.http_method
  status_code = "200"

  # Transforms the backend JSON response to XML
  response_templates = {
    "application/xml" = <<EOF
#set($inputRoot = $input.path('$'))
<?xml version="1.0" encoding="UTF-8"?>
<message>
    $inputRoot.body
</message>
EOF
  }
  depends_on = [
    aws_api_gateway_integration.theapp-listtablesintegration
  ]
}

resource "aws_api_gateway_integration_response" "theapp-calldb-integrationresponse" {
  rest_api_id = aws_api_gateway_rest_api.theapp-cognito.id
  resource_id = aws_api_gateway_resource.theapp-calldb.id
  http_method = aws_api_gateway_method.theapp-calldbpost.http_method
  status_code = "200"

  # Transforms the backend JSON response to XML
  response_templates = {
    "application/xml" = <<EOF
#set($inputRoot = $input.path('$'))
<?xml version="1.0" encoding="UTF-8"?>
<message>
    $inputRoot.body
</message>
EOF
  }
  depends_on = [
    aws_api_gateway_integration.theapp-calldbintegration
  ]
}

############## lambda permissions for the API ##############
resource "aws_lambda_permission" "apigw_lambda_redirect" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.theapp-redirect.function_name
  principal     = "apigateway.amazonaws.com"

  # More: http://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-control-access-using-iam-policies-to-invoke-api.html
  source_arn = "arn:aws:execute-api:${var.region}:${var.account_id}:${aws_api_gateway_rest_api.theapp-cognito.id}/*/${aws_api_gateway_method.theapp-redirectget.http_method}${aws_api_gateway_resource.theapp-redirect.path}"
}

resource "aws_lambda_permission" "apigw_lambda_redirect2" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.theapp-redirect2.function_name
  principal     = "apigateway.amazonaws.com"

  # More: http://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-control-access-using-iam-policies-to-invoke-api.html
  source_arn = "arn:aws:execute-api:${var.region}:${var.account_id}:${aws_api_gateway_rest_api.theapp-cognito.id}/*/${aws_api_gateway_method.theapp-redirect2get.http_method}${aws_api_gateway_resource.theapp-redirect2.path}"
}

resource "aws_lambda_permission" "apigw_lambda_main" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.theapp-main.function_name
  principal     = "apigateway.amazonaws.com"

  # More: http://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-control-access-using-iam-policies-to-invoke-api.html
  source_arn = "arn:aws:execute-api:${var.region}:${var.account_id}:${aws_api_gateway_rest_api.theapp-cognito.id}/*/${aws_api_gateway_method.theapp-mainpost.http_method}${aws_api_gateway_resource.theapp-main.path}"
}

resource "aws_lambda_permission" "apigw_lambda_describetable" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.theapp-dynamodbDescribeTable.function_name
  principal     = "apigateway.amazonaws.com"

  # More: http://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-control-access-using-iam-policies-to-invoke-api.html
  source_arn = "arn:aws:execute-api:${var.region}:${var.account_id}:${aws_api_gateway_rest_api.theapp-cognito.id}/*/${aws_api_gateway_method.theapp-describetablepost.http_method}${aws_api_gateway_resource.theapp-describetable.path}"
}

resource "aws_lambda_permission" "apigw_lambda_listtables" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.theapp-ListTables.function_name
  principal     = "apigateway.amazonaws.com"

  # More: http://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-control-access-using-iam-policies-to-invoke-api.html
  source_arn = "arn:aws:execute-api:${var.region}:${var.account_id}:${aws_api_gateway_rest_api.theapp-cognito.id}/*/${aws_api_gateway_method.theapp-listtablespost.http_method}${aws_api_gateway_resource.theapp-listtables.path}"
}

resource "aws_lambda_permission" "apigw_lambda_calldb" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.theapp-dynamodb.function_name
  principal     = "apigateway.amazonaws.com"

  # More: http://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-control-access-using-iam-policies-to-invoke-api.html
  source_arn = "arn:aws:execute-api:${var.region}:${var.account_id}:${aws_api_gateway_rest_api.theapp-cognito.id}/*/${aws_api_gateway_method.theapp-calldbpost.http_method}${aws_api_gateway_resource.theapp-calldb.path}"
}

############## API deployment ##############
resource "aws_api_gateway_deployment" "TheApp" {
  rest_api_id = aws_api_gateway_rest_api.theapp-cognito.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.theapp-redirect.id,
      aws_api_gateway_resource.theapp-redirect2.id,
      aws_api_gateway_resource.theapp-main.id,
      aws_api_gateway_resource.theapp-describetable.id,
      aws_api_gateway_resource.theapp-listtables.id,
      aws_api_gateway_resource.theapp-calldb.id,
      aws_api_gateway_method.theapp-redirectget.id,
      aws_api_gateway_method.theapp-redirect2get.id,
      aws_api_gateway_method.theapp-mainpost.id,
      aws_api_gateway_method.theapp-describetablepost.id,
      aws_api_gateway_method.theapp-listtablespost.id,
      aws_api_gateway_method.theapp-calldbpost.id,
      aws_api_gateway_integration.theapp-redirectintegration.id,
      aws_api_gateway_integration.theapp-redirect2integration.id,
      aws_api_gateway_integration.theapp-mainintegration.id,
      aws_api_gateway_integration.theapp-describetableintegration.id,
      aws_api_gateway_integration.theapp-listtablesintegration.id,
      aws_api_gateway_integration.theapp-calldbintegration.id
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

############## API deployment stage ##############
resource "aws_api_gateway_stage" "TheApp" {
  deployment_id = aws_api_gateway_deployment.TheApp.id
  rest_api_id   = aws_api_gateway_rest_api.theapp-cognito.id
  stage_name    = lower(var.var_env)
}

############## Set up output needed for SAML configuration ##############
output "clientdata" {
  value = [
    "UserPoolID = ${aws_cognito_user_pool.theapp-lambda-SAML.id}",
    "RelayState = https://${aws_api_gateway_rest_api.theapp-cognito.id}.execute-api.${var.region}.amazonaws.com",
    "DomainPrefix = ${aws_cognito_user_pool_domain.theapp.domain}",
    "Region = ${var.region}"
  ]
}

output "authendpoint" {
  value = "https://${aws_cognito_user_pool_domain.theapp.domain}.auth.${var.region}.amazoncognito.com/login?client_id=${aws_cognito_user_pool_client.theapp-lambda-SAML-client-noSecret.id}&response_type=code&scope=aws.cognito.signin.user.admin+email+mainapi/api+openid+phone&redirect_uri=https://${aws_api_gateway_rest_api.theapp-cognito.id}.execute-api.${var.region}.amazonaws.com/${lower(var.var_env)}/redirect"
}

output "authendpointNonce" {
  value = "https://${aws_cognito_user_pool_domain.theapp.domain}.auth.${var.region}.amazoncognito.com/login?client_id=${aws_cognito_user_pool_client.theapp-lambda-SAML-client-noSecret-allowNonce.id}&response_type=code&scope=aws.cognito.signin.user.admin+email+mainapi/api+mainapi/nonce+openid+phone&redirect_uri=https://${aws_api_gateway_rest_api.theapp-cognito.id}.execute-api.${var.region}.amazonaws.com/${lower(var.var_env)}/redirect2"
}
