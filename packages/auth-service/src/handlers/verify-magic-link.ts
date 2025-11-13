import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, GetCommand, PutCommand, UpdateCommand } from '@aws-sdk/lib-dynamodb';
import { nanoid } from 'nanoid';
import { createJWT } from '../utils/jwt.js';
import type { VerifyMagicLinkRequest, MagicLinkToken, User } from '../types.js';

const ddbClient = new DynamoDBClient({});
const ddb = DynamoDBDocumentClient.from(ddbClient);

const TOKENS_TABLE = process.env.TOKENS_TABLE || '';
const USERS_TABLE = process.env.USERS_TABLE || '';

export async function verifyMagicLink(
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> {
  try {
    const body: VerifyMagicLinkRequest = JSON.parse(event.body || '{}');

    if (!body.token) {
      return {
        statusCode: 400,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Token is required' }),
      };
    }

    // Get token from DynamoDB
    const tokenResult = await ddb.send(
      new GetCommand({
        TableName: TOKENS_TABLE,
        Key: { token: body.token },
      })
    );

    const tokenData = tokenResult.Item as MagicLinkToken | undefined;

    if (!tokenData) {
      return {
        statusCode: 404,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Invalid or expired token' }),
      };
    }

    // Check if token has been used
    if (tokenData.used) {
      return {
        statusCode: 400,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Token has already been used' }),
      };
    }

    // Check if token has expired
    if (Date.now() > tokenData.expiresAt) {
      return {
        statusCode: 400,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Token has expired' }),
      };
    }

    // Mark token as used
    await ddb.send(
      new UpdateCommand({
        TableName: TOKENS_TABLE,
        Key: { token: body.token },
        UpdateExpression: 'SET #used = :true',
        ExpressionAttributeNames: { '#used': 'used' },
        ExpressionAttributeValues: { ':true': true },
      })
    );

    // Get or create user
    const userResult = await ddb.send(
      new GetCommand({
        TableName: USERS_TABLE,
        Key: { email: tokenData.email },
      })
    );

    let user = userResult.Item as User | undefined;

    if (!user) {
      // Create new user
      user = {
        userId: nanoid(),
        email: tokenData.email,
        createdAt: Date.now(),
        lastLoginAt: Date.now(),
      };

      await ddb.send(
        new PutCommand({
          TableName: USERS_TABLE,
          Item: user,
        })
      );
    } else {
      // Update last login time
      await ddb.send(
        new UpdateCommand({
          TableName: USERS_TABLE,
          Key: { email: tokenData.email },
          UpdateExpression: 'SET lastLoginAt = :now',
          ExpressionAttributeValues: { ':now': Date.now() },
        })
      );
    }

    // Create JWT
    const jwtToken = createJWT({
      userId: user.userId,
      email: user.email,
    });

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        token: jwtToken,
        user: {
          userId: user.userId,
          email: user.email,
        },
      }),
    };
  } catch (error) {
    console.error('Error verifying magic link:', error);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        error: 'Failed to verify magic link',
        message: error instanceof Error ? error.message : 'Unknown error',
      }),
    };
  }
}
