import jwt from 'jsonwebtoken';
import type { JWTPayload } from '../types.js';

const JWT_SECRET = process.env.JWT_SECRET || 'dev-secret-change-in-production';
const JWT_EXPIRY = '7d'; // 7 days

export function createJWT(payload: Omit<JWTPayload, 'iat' | 'exp'>): string {
  return jwt.sign(payload, JWT_SECRET, {
    expiresIn: JWT_EXPIRY,
  });
}

export function verifyJWT(token: string): JWTPayload | null {
  try {
    const decoded = jwt.verify(token, JWT_SECRET) as JWTPayload;
    return decoded;
  } catch (error) {
    console.error('JWT verification failed:', error);
    return null;
  }
}
