const sqlite3 = require('sqlite3').verbose();

// Thin promise wrapper around sqlite3's callback API so models/services can
// use async/await instead of nested callbacks. The connection is created here
// (composition root owns the instance) and injected into models, instead of
// being read from a mutable module-level global.
class Database {
    constructor(filename = ':memory:') {
        this.raw = new sqlite3.Database(filename);
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.raw.run(sql, params, function callback(err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    get(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.raw.get(sql, params, (err, row) => {
                if (err) return reject(err);
                resolve(row);
            });
        });
    }

    all(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.raw.all(sql, params, (err, rows) => {
                if (err) return reject(err);
                resolve(rows);
            });
        });
    }

    serialize(fn) {
        this.raw.serialize(fn);
    }
}

module.exports = Database;
