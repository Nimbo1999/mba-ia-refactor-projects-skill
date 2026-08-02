const express = require('express');
const { config } = require('./config/env');
const logger = require('./config/logger');
const Database = require('./db/connection');
const { migrate, seed } = require('./db/schema');
const passwordService = require('./services/passwordService');
const errorHandler = require('./middlewares/errorHandler');

const UserModel = require('./models/userModel');
const CourseModel = require('./models/courseModel');
const EnrollmentModel = require('./models/enrollmentModel');
const PaymentModel = require('./models/paymentModel');
const AuditLogModel = require('./models/auditLogModel');

const CacheService = require('./services/cacheService');
const { CheckoutService } = require('./services/checkoutService');
const FinancialReportService = require('./services/financialReportService');
const UserService = require('./services/userService');

const CheckoutController = require('./controllers/checkoutController');
const FinancialReportController = require('./controllers/financialReportController');
const UserController = require('./controllers/userController');

const checkoutRoutes = require('./routes/checkoutRoutes');
const adminRoutes = require('./routes/adminRoutes');
const userRoutes = require('./routes/userRoutes');

// Composition root: creates the DB connection, wires
// models -> services -> controllers -> routes via explicit dependency
// injection (no module-level mutable globals), and returns the initialized
// Express app plus the raw db handle so the caller can run migrations/seeds.
function buildApp() {
    const db = new Database(':memory:');

    const userModel = new UserModel(db);
    const courseModel = new CourseModel(db);
    const enrollmentModel = new EnrollmentModel(db);
    const paymentModel = new PaymentModel(db);
    const auditLogModel = new AuditLogModel(db);

    const cacheService = new CacheService();
    const checkoutService = new CheckoutService({
        userModel,
        courseModel,
        enrollmentModel,
        paymentModel,
        auditLogModel,
        cacheService,
    });
    const financialReportService = new FinancialReportService({ enrollmentModel });
    const userService = new UserService({ userModel, enrollmentModel, paymentModel });

    const checkoutController = new CheckoutController({ checkoutService });
    const financialReportController = new FinancialReportController({ financialReportService });
    const userController = new UserController({ userService });

    const app = express();
    app.use(express.json());

    app.use('/api', checkoutRoutes(checkoutController));
    app.use('/api', adminRoutes(financialReportController));
    app.use('/api', userRoutes(userController));

    app.use(errorHandler);

    return { app, db };
}

async function bootstrap() {
    const { app, db } = buildApp();

    await migrate(db);
    await seed(db, passwordService);

    app.listen(config.port, () => {
        logger.info(`LMS API running on port ${config.port}`);
    });

    return app;
}

if (require.main === module) {
    bootstrap().catch((err) => {
        logger.error('Failed to bootstrap application', { message: err.message });
        process.exit(1);
    });
}

module.exports = { buildApp, bootstrap };
