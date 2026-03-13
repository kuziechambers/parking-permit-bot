resource "aws_lambda_function" "parking_permit_bot_lambda" {
  function_name = "parking-permit-bot"
  role          = aws_iam_role.lambda_role.arn

  tags = {
    ManagedBy = "terraform"
  }
}