/**
 * NUBAN (Nigeria Uniform Bank Account Number) utility.
 *
 * Format: [3-digit bank code][6-digit serial][1 check digit] = 10 digits
 *
 * CBN check-digit algorithm:
 *   1. Concatenate bank code (3 digits) + serial (6 digits) → 9 digits
 *   2. Multiply each digit by the corresponding weight [3,7,3,3,7,3,3,7,3]
 *   3. Sum the products
 *   4. check_digit = (10 − (sum % 10)) % 10
 */

export const BANK_CODE = '999'; // NeuraPay demo bank code

const NUBAN_WEIGHTS = [3, 7, 3, 3, 7, 3, 3, 7, 3] as const;

function computeCheckDigit(bankCode: string, serial: string): number {
  const digits = `${bankCode}${serial}`.split('').map(Number);
  const sum = digits.reduce((acc, d, i) => acc + d * NUBAN_WEIGHTS[i], 0);
  return (10 - (sum % 10)) % 10;
}

/**
 * Generate a 10-digit NUBAN account number for a given 1-based sequence number.
 * sequenceNumber must be between 1 and 999_999 inclusive.
 */
export function generateAccountNumber(sequenceNumber: number): string {
  if (sequenceNumber < 1 || sequenceNumber > 999_999) {
    throw new Error(`Sequence number ${sequenceNumber} is out of valid range (1–999999)`);
  }
  const serial = String(sequenceNumber).padStart(6, '0');
  const checkDigit = computeCheckDigit(BANK_CODE, serial);
  return `${BANK_CODE}${serial}${checkDigit}`;
}
