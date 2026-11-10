const crypto = require('node:crypto');

const KEY_LENGTH = 64;

function hashPassword(password) {
    const salt = crypto.randomBytes(16).toString('hex');
    const hash = crypto.scryptSync(password, salt, KEY_LENGTH).toString('hex');
    return `scrypt$${salt}$${hash}`;
}

function verifyPassword(password, stored) {
    const [scheme, salt, hash] = String(stored).split('$');
    if (scheme !== 'scrypt' || !salt || !hash) return false;
    const expected = Buffer.from(hash, 'hex');
    const actual = crypto.scryptSync(password, salt, expected.length);
    return crypto.timingSafeEqual(actual, expected);
}

// Para cadastros sem senha informada: ninguém conhece o valor gerado.
function randomPassword() {
    return crypto.randomBytes(24).toString('base64url');
}

module.exports = { hashPassword, verifyPassword, randomPassword };
