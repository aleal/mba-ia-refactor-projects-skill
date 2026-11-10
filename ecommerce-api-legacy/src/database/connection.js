const sqlite3 = require('sqlite3');
const { createSchema, seedIfEmpty } = require('./schema');

// Wrapper com Promises sobre a conexão única do sqlite3.
function wrap(raw) {
    const run = (sql, params = []) => new Promise((resolve, reject) => {
        raw.run(sql, params, function onRun(err) {
            if (err) return reject(err);
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
    const get = (sql, params = []) => new Promise((resolve, reject) => {
        raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });
    const all = (sql, params = []) => new Promise((resolve, reject) => {
        raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });
    const close = () => new Promise((resolve, reject) => {
        raw.close((err) => (err ? reject(err) : resolve()));
    });

    // A conexão é compartilhada: transações são enfileiradas para não se intercalarem.
    let queue = Promise.resolve();
    function transaction(work) {
        const result = queue.then(async () => {
            await run('BEGIN');
            try {
                const value = await work();
                await run('COMMIT');
                return value;
            } catch (err) {
                await run('ROLLBACK');
                throw err;
            }
        });
        queue = result.catch(() => {});
        return result;
    }

    return { run, get, all, close, transaction };
}

async function openDatabase(path) {
    const raw = await new Promise((resolve, reject) => {
        const conn = new sqlite3.Database(path, (err) => (err ? reject(err) : resolve(conn)));
    });
    const db = wrap(raw);
    await db.run('PRAGMA foreign_keys = ON');
    await createSchema(db);
    await seedIfEmpty(db);
    return db;
}

module.exports = { openDatabase };
