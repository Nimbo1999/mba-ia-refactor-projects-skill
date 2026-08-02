// Data access for the `audit_logs` table.
class AuditLogModel {
  constructor(db) {
    this.db = db;
  }

  create(action) {
    return this.db.run(
      "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
      [action]
    );
  }
}

module.exports = AuditLogModel;
