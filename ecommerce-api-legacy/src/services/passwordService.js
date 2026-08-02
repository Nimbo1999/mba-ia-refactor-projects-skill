const bcrypt = require('bcryptjs');

// Real, one-way password hashing (replaces the previous reversible
// "badCrypto" scheme). Salt rounds kept moderate for a demo/legacy project.
const SALT_ROUNDS = 10;

async function hash(plainTextPassword) {
    return bcrypt.hash(plainTextPassword, SALT_ROUNDS);
}

async function compare(plainTextPassword, passwordHash) {
    return bcrypt.compare(plainTextPassword, passwordHash);
}

module.exports = { hash, compare };
