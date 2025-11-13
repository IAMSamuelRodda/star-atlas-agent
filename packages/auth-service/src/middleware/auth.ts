import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { verifyJWT } from '../utils/jwt.js';
import { logger } from '../utils/logger.js';
import type { AuthenticatedRequest } from '../types.js';

export interface AuthenticatedEvent extends APIGatewayProxyEvent {
  auth?: AuthenticatedRequest;
}

export function authMiddleware(
  // eslint-disable-next-line no-unused-vars
  handler: (event: AuthenticatedEvent) => Promise<APIGatewayProxyResult>
) {
  return async (event: AuthenticatedEvent): Promise<APIGatewayProxyResult> => {
    try {
      // Extract token from Authorization header
      const authHeader = event.headers?.['Authorization'] || event.headers?.['authorization'];

      if (!authHeader) {
        return {
          statusCode: 401,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ error: 'Missing authorization header' }),
        };
      }

      // Expect format: "Bearer <token>"
      const [bearer, token] = authHeader.split(' ');

      if (bearer !== 'Bearer' || !token) {
        return {
          statusCode: 401,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ error: 'Invalid authorization format. Expected: Bearer <token>' }),
        };
      }

      // Verify JWT
      const payload = verifyJWT(token);

      if (!payload) {
        return {
          statusCode: 401,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ error: 'Invalid or expired token' }),
        };
      }

      // Add auth data to event
      event.auth = {
        userId: payload.userId,
        email: payload.email,
      };

      // Call the handler with authenticated event
      return await handler(event);
    } catch (error) {
      logger.error(
        'Auth middleware error',
        {},
        error instanceof Error ? error : new Error(String(error))
      );
      return {
        statusCode: 500,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          error: 'Internal server error',
          message: error instanceof Error ? error.message : 'Unknown error',
        }),
      };
    }
  };
}
