resource "aws_dynamodb_table" "parking_permits_table" {
  name           = "parking-registration-permits"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "firstName"

  attribute {
    name = "firstName"
    type = "S"
  }

  tags = {
    ManagedBy = "terraform"
  }
}
