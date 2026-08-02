const logger = require('../config/logger');
const passwordService = require('./passwordService');
const { config } = require('../config/env');

const PAYMENT_STATUS = { PAID: 'PAID', DENIED: 'DENIED' };
// Test-gateway convention kept from the original flow: card numbers starting
// with this digit are approved. Named here instead of a bare magic string.
const APPROVED_CARD_PREFIX = '4';
const DEFAULT_NEW_USER_PASSWORD = '123456';

class CheckoutError extends Error {
    constructor(message, status) {
        super(message);
        this.status = status;
    }
}

// Orchestrates the checkout business flow: course lookup, user
// creation/reuse, payment decision, enrollment and audit logging. Extracted
// out of the HTTP controller so it can be tested and reused independently of
// Express.
class CheckoutService {
    constructor({ userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, cacheService }) {
        this.userModel = userModel;
        this.courseModel = courseModel;
        this.enrollmentModel = enrollmentModel;
        this.paymentModel = paymentModel;
        this.auditLogModel = auditLogModel;
        this.cacheService = cacheService;
    }

    async checkout({ username, email, password, courseId, cardNumber }) {
        const course = await this.courseModel.findActiveById(courseId);
        if (!course) {
            throw new CheckoutError('Curso não encontrado', 404);
        }

        const userId = await this._resolveUserId({ username, email, password });

        logger.info('Processing payment', { courseId, gatewayKey: this._maskedGatewayKey() });
        const paymentStatus = cardNumber.startsWith(APPROVED_CARD_PREFIX)
            ? PAYMENT_STATUS.PAID
            : PAYMENT_STATUS.DENIED;

        if (paymentStatus === PAYMENT_STATUS.DENIED) {
            throw new CheckoutError('Pagamento recusado', 400);
        }

        const enrollmentId = await this.enrollmentModel.create({ userId, courseId });
        await this.paymentModel.create({ enrollmentId, amount: course.price, status: paymentStatus });
        await this.auditLogModel.create(`Checkout curso ${courseId} por ${userId}`);

        this.cacheService.set(`last_checkout_${userId}`, course.title);

        return { enrollmentId };
    }

    async _resolveUserId({ username, email, password }) {
        const existingUser = await this.userModel.findByEmail(email);
        if (existingUser) {
            return existingUser.id;
        }

        const passwordHash = await passwordService.hash(password || DEFAULT_NEW_USER_PASSWORD);
        return this.userModel.create({ name: username, email, passwordHash });
    }

    // Never log/expose the real secret — only confirm a key is configured.
    _maskedGatewayKey() {
        return config.paymentGatewayKey ? '***configured***' : '***missing***';
    }
}

module.exports = { CheckoutService, CheckoutError };
