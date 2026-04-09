/**
 * Generate a UUID v4 (random UUID)
 * Uses native crypto.randomUUID() if available
 * 
 * @returns {string} - A UUID like "550e8400-e29b-41d4-a716-446655440000"
 */
export function generateUUID() {
  return crypto.randomUUID();
}
