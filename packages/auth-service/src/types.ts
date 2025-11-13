export interface MagicLinkToken {
  token: string;
  email: string;
  createdAt: number;
  expiresAt: number;
  used: boolean;
}

export interface JWTPayload {
  userId: string;
  email: string;
  iat: number;
  exp: number;
}

export interface User {
  userId: string;
  email: string;
  createdAt: number;
  lastLoginAt: number;
  walletAddress?: string;
}

export interface SendMagicLinkRequest {
  email: string;
}

export interface VerifyMagicLinkRequest {
  token: string;
}

export interface AuthenticatedRequest {
  userId: string;
  email: string;
}
