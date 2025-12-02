# 일일 티켓팅 Lambda 함수
resource "aws_lambda_function" "daily_ticketing" {
  filename         = "daily_ticketing.zip"
  function_name    = "refresh-plus-daily-ticketing"
  role            = aws_iam_role.lambda_role.arn
  handler         = "daily_ticketing.handler"
  runtime         = "python3.11"
  timeout         = 60
  memory_size     = 512

  environment {
    variables = {
      DATABASE_URL = var.database_url
      ENVIRONMENT = var.environment
      SENTRY_DSN = var.sentry_dsn
    }
  }
}

# 점수 회복 Lambda 함수
resource "aws_lambda_function" "score_recovery" {
  filename         = "score_recovery.zip"
  function_name    = "refresh-plus-score-recovery"
  role            = aws_iam_role.lambda_role.arn
  handler         = "score_recovery.handler"
  runtime         = "python3.11"
  timeout         = 60
  memory_size     = 512

  environment {
    variables = {
      DATABASE_URL = var.database_url
      ENVIRONMENT = var.environment
      SENTRY_DSN = var.sentry_dsn
    }
  }
}

# Lambda IAM Role
resource "aws_iam_role" "lambda_role" {
  name = "refresh-plus-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
