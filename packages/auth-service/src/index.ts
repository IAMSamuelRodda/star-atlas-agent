export * from './types.js';
export { sendMagicLink } from './handlers/send-magic-link.js';
export { verifyMagicLink } from './handlers/verify-magic-link.js';
export { createWalletChallenge } from './handlers/wallet-challenge.js';
export { verifyWalletSignature } from './handlers/wallet-verify.js';
export { getProfile } from './handlers/get-profile.js';
export { updateProfile } from './handlers/update-profile.js';
export { createJWT, verifyJWT } from './utils/jwt.js';
export { authMiddleware } from './middleware/auth.js';
