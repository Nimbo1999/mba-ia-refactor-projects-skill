// Orchestrates user deletion, cleaning up dependent enrollments/payments
// instead of leaving orphaned rows behind (previous behavior left dirty data).
class UserService {
    constructor({ userModel, enrollmentModel, paymentModel }) {
        this.userModel = userModel;
        this.enrollmentModel = enrollmentModel;
        this.paymentModel = paymentModel;
    }

    async deleteUser(userId) {
        // Payments reference enrollments, so they must be removed first.
        await this.paymentModel.deleteByEnrollmentUserId(userId);
        await this.enrollmentModel.deleteByUserId(userId);
        await this.userModel.delete(userId);
    }
}

module.exports = UserService;
