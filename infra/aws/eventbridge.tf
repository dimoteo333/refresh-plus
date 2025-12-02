# AWS EventBridge 설정

# 일일 티켓팅 - 매일 00:00 (UTC+9)
resource "aws_cloudwatch_event_rule" "daily_ticketing" {
  name                = "refresh-plus-daily-ticketing"
  description         = "Trigger daily ticketing at midnight KST"
  schedule_expression = "cron(0 15 * * ? *)"  # UTC 기준 15:00 = KST 00:00
}

resource "aws_cloudwatch_event_target" "daily_ticketing" {
  rule      = aws_cloudwatch_event_rule.daily_ticketing.name
  target_id = "DailyTicketingLambda"
  arn       = aws_lambda_function.daily_ticketing.arn
}

resource "aws_lambda_permission" "allow_eventbridge_daily_ticketing" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.daily_ticketing.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_ticketing.arn
}

# 점수 회복 - 매시간
resource "aws_cloudwatch_event_rule" "score_recovery" {
  name                = "refresh-plus-score-recovery"
  description         = "Trigger score recovery every hour"
  schedule_expression = "cron(0 * * * ? *)"
}

resource "aws_cloudwatch_event_target" "score_recovery" {
  rule      = aws_cloudwatch_event_rule.score_recovery.name
  target_id = "ScoreRecoveryLambda"
  arn       = aws_lambda_function.score_recovery.arn
}

resource "aws_lambda_permission" "allow_eventbridge_score_recovery" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.score_recovery.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.score_recovery.arn
}
