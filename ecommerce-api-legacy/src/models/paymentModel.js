// Data access for the `payments` table.
class PaymentModel {
    constructor(db) {
        this.db = db;
    }

    async create({ enrollmentId, amount, status }) {
        const { lastID } = await this.db.run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollmentId, amount, status]
        );
        return lastID;
    }

    deleteByEnrollmentUserId(userId) {
        return this.db.run(
            `DELETE FROM payments WHERE enrollment_id IN (
                SELECT id FROM enrollments WHERE user_id = ?
            )`,
            [userId]
        );
    }
}

module.exports = PaymentModel;
