resource "aws_ecr_repository" "parking_permit_bot_ecr" {
  name                 = "${var.lambda_name}-ecr"
  image_tag_mutability = "MUTABLE"

  tags = {
    ManagedBy = "terraform"
  }
}

resource "aws_lambda_function" "parking_permit_bot_lambda" {
  function_name = var.lambda_name
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.parking_permit_bot.repository_url}:latest"
  timeout       = 300
  memory_size   = 1024

  tags = {
    ManagedBy = "terraform"
  }
}