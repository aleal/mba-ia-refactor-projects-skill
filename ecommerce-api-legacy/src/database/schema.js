const { hashPassword } = require('../utils/password');
const { PAYMENT_STATUS } = require('../config/constants');

async function createSchema(db) {
    await db.run(`CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, pass TEXT)`);
    await db.run(`CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)`);
    await db.run(`CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE)`);
    await db.run(`CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY,
        enrollment_id INTEGER REFERENCES enrollments(id) ON DELETE CASCADE,
        amount REAL, status TEXT)`);
    await db.run(`CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)`);
}

async function seedIfEmpty(db) {
    const { count } = await db.get('SELECT COUNT(*) AS count FROM users');
    if (count > 0) return;

    await db.transaction(async () => {
        await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            ['Leonan', 'leonan@fullcycle.com.br', hashPassword('123')]);
        await db.run('INSERT INTO courses (title, price, active) VALUES (?, ?, 1), (?, ?, 1)',
            ['Clean Architecture', 997.00, 'Docker', 497.00]);
        await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
        await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (1, ?, ?)',
            [997.00, PAYMENT_STATUS.PAID]);
    });
}

module.exports = { createSchema, seedIfEmpty };
