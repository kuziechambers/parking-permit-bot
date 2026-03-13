data "aws_caller_identity" "current" {}

variable "lambda_name" {
  default = "parking-permit-bot"
}

variable "lambda_name_upper" {
  default = "ParkingPermitBot"
}

variable "s3_bucket_name" {
  default = "parking-registration-screenshots"
}