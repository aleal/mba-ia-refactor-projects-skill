const express = require('express');
const UserModel = require('./models/userModel');
const CourseModel = require('./models/courseModel');
const EnrollmentModel = require('./models/enrollmentModel');
const PaymentModel = require('./models/paymentModel');
const AuditLogModel = require('./models/auditLogModel');
const ReportModel = require('./models/reportModel');
const PaymentGateway = require('./services/paymentGateway');
const CheckoutService = require('./services/checkoutService');
const CheckoutController = require('./controllers/checkoutController');
const ReportController = require('./controllers/reportController');
const UserController = require('./controllers/userController');
const { requireAdmin } = require('./middlewares/auth');
const { createErrorHandler } = require('./middlewares/errorHandler');
const buildRoutes = require('./routes');

// Composition root: monta models, services e controllers sobre o db e a config recebidos.
function createApp({ db, config, logger }) {
    const users = new UserModel(db);
    const checkoutService = new CheckoutService({
        db,
        users,
        courses: new CourseModel(db),
        enrollments: new EnrollmentModel(db),
        payments: new PaymentModel(db),
        auditLogs: new AuditLogModel(db),
        paymentGateway: new PaymentGateway({ apiKey: config.paymentGatewayKey, logger }),
    });

    const app = express();
    app.use(express.json());
    app.use(buildRoutes({
        checkoutController: new CheckoutController({ checkoutService }),
        reportController: new ReportController({ reports: new ReportModel(db) }),
        userController: new UserController({ users }),
        requireAdmin: requireAdmin(config),
    }));
    app.use(createErrorHandler(logger));
    return app;
}

module.exports = { createApp };
