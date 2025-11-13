export * from './types.js';
export { sendMagicLink } from './handlers/send-magic-link.js';
export { verifyMagicLink } from './handlers/verify-magic-link.js';
export { createJWT, verifyJWT } from './utils/jwt.js';
export { authMiddleware } from './middleware/auth.js';
