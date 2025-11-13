# API Gateway HTTP API Configuration

# HTTP API (cheaper than REST API, perfect for serverless)
resource "aws_apigatewayv2_api" "main" {
  name          = "${var.project_name}-api-${var.environment}"
  protocol_type = "HTTP"
  description   = "Star Atlas Agent HTTP API"

  cors_configuration {
    allow_origins = var.environment == "prod" ? ["https://staratlas-agent.com"] : ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization", "X-User-Id"]
    max_age       = 300
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-api-${var.environment}"
  })
}

# Default stage (auto-deploy)
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }

  tags = var.tags
}

# CloudWatch log group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${var.project_name}-${var.environment}"
  retention_in_days = var.environment == "prod" ? 30 : 7

  tags = var.tags
}

# Lambda integrations
resource "aws_apigatewayv2_integration" "agent_core" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"

  connection_type      = "INTERNET"
  description          = "Agent Core Lambda integration"
  integration_method   = "POST"
  integration_uri      = module.agent_core_lambda.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "memory_service" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"

  connection_type      = "INTERNET"
  description          = "Memory Service Lambda integration"
  integration_method   = "POST"
  integration_uri      = module.memory_service_lambda.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "mcp_server" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"

  connection_type      = "INTERNET"
  description          = "MCP Server Lambda integration"
  integration_method   = "POST"
  integration_uri      = module.mcp_server_lambda.invoke_arn
  payload_format_version = "2.0"
}

# Routes
resource "aws_apigatewayv2_route" "agent_chat" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /agent/chat"
  target    = "integrations/${aws_apigatewayv2_integration.agent_core.id}"
}

resource "aws_apigatewayv2_route" "memory_query" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /memory/query"
  target    = "integrations/${aws_apigatewayv2_integration.memory_service.id}"
}

resource "aws_apigatewayv2_route" "memory_store" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /memory/store"
  target    = "integrations/${aws_apigatewayv2_integration.memory_service.id}"
}

resource "aws_apigatewayv2_route" "mcp_tools" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /mcp/tools"
  target    = "integrations/${aws_apigatewayv2_integration.mcp_server.id}"
}

resource "aws_apigatewayv2_route" "mcp_execute" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /mcp/execute"
  target    = "integrations/${aws_apigatewayv2_integration.mcp_server.id}"
}

resource "aws_apigatewayv2_route" "health_check" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /health"
  target    = "integrations/${aws_apigatewayv2_integration.agent_core.id}"
}

# Lambda permissions for API Gateway
resource "aws_lambda_permission" "agent_core_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.agent_core_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "memory_service_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.memory_service_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "mcp_server_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.mcp_server_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}
