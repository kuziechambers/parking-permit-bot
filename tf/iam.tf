# trust policy to assume the role
data "aws_iam_policy_document" "lambda_trust_policy" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

# execution role
resource "aws_iam_role" "lambda_role" {
  name               = "${var.lambda_name}-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust_policy.json

  tags = {
    Service   = "lambda"
    Resource  = "${var.lambda_name}-lambda"
    ManagedBy = "terraform"
  }
}

# execution policy (CloudWatch Logs)
resource "aws_iam_policy" "cloudwatch_policy" {
  name = "AWSLambda${var.lambda_name_upper}CloudWatchPolicy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CreateCloudWatchLogGroups"
        Effect = "Allow"
        Action = ["logs:CreateLogGroup"]
        Resource = [
          "arn:aws:logs:us-east-1:${data.aws_caller_identity.current.account_id}:*",
        ]
      },
      {
        Sid    = "CreateCloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "arn:aws:logs:us-east-1:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.lambda_name}:*",
        ]
      }
    ]
  })

  tags = {
    Service   = "lambda"
    ManagedBy = "terraform"
  }
}

resource "aws_iam_role_policy_attachment" "lambda_cloudwatch_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.cloudwatch_policy.arn
}

# execution policy (DynamoDB)
resource "aws_iam_policy" "dynamodb_policy" {
  name = "AWSLambda${var.lambda_name_upper}DynamoDBPolicy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DynamoDBAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:DeleteItem",
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
        ]
        Resource = [
          aws_dynamodb_table.parking_permits_table.arn,
        ]
      }
    ]
  })

  tags = {
    Service   = "lambda"
    ManagedBy = "terraform"
  }
}

resource "aws_iam_role_policy_attachment" "lambda_dynamodb_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.dynamodb_policy.arn
}

# execution policy (S3)
resource "aws_iam_policy" "s3_policy" {
  name = "AWSLambda${var.lambda_name_upper}S3Policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3Access"
        Effect = "Allow"
        Action = [
          "s3:DeleteObject",
          "s3:GetObject",
          "s3:PutObject",
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_name}",
        ]
      }
    ]
  })

  tags = {
    Service   = "lambda"
    ManagedBy = "terraform"
  }
}

resource "aws_iam_role_policy_attachment" "lambda_s3_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.s3_policy.arn
}
