variable "account_id" {
  type = string
}
variable "region" {
  default = "us-east-1"
}
variable "var_env" {
  type = string
}
variable "var_redirect_version" {
  default = "1.0"
}
variable "var_redirect2_version" {
  default = "1.0"
}
variable "var_dynamodb_version" {
  default = "1.0"
}
variable "var_dynamodbDescribeTable_version" {
  default = "1.0"
}
variable "var_ListTables_version" {
  default = "1.0"
}
variable "var_main_version" {
  default = "1.0"
}
