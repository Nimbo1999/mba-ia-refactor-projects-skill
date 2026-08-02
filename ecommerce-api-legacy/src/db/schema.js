// Schema definition and seed data, isolated from the entity models so that
// each model only knows queries relevant to its own domain.
async function migrate(db) {
    await db.run(
        'CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, password_hash TEXT)'
    );
    await db.run(
        'CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)'
    );
    await db.run(
        'CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)'
    );
    await db.run(
        'CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)'
    );
    await db.run(
        'CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)'
    );
}

async function seed(db, passwordHasher) {
    const passwordHash = await passwordHasher.hash('123');

    await db.run(
        'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
        ['Leonan', 'leonan@fullcycle.com.br', passwordHash]
    );
    await db.run(
        "INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)"
    );
    await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
    await db.run(
        "INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')"
    );
}

module.exports = { migrate, seed };
