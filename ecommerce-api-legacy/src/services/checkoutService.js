const { AppError } = require('../middlewares/errorHandler');
const { PAYMENT_STATUS } = require('../config/constants');
const { hashPassword, randomPassword } = require('../utils/password');

class CheckoutService {
    constructor({ db, users, courses, enrollments, payments, auditLogs, paymentGateway }) {
        Object.assign(this, { db, users, courses, enrollments, payments, auditLogs, paymentGateway });
    }

    async checkout({ name, email, password, courseId, cardNumber }) {
        const course = await this.courses.findActiveById(courseId);
        if (!course) throw new AppError('Curso não encontrado', 404);

        const status = this.paymentGateway.charge(cardNumber, course.price);
        if (status === PAYMENT_STATUS.DENIED) throw new AppError('Pagamento recusado', 400);

        return this.db.transaction(async () => {
            const existing = await this.users.findByEmail(email);
            const userId = existing
                ? existing.id
                : await this.users.create({ name, email, passwordHash: hashPassword(password || randomPassword()) });

            const enrollmentId = await this.enrollments.create(userId, course.id);
            await this.payments.create(enrollmentId, course.price, status);
            await this.auditLogs.log(`Checkout curso ${course.id} por ${userId}`);
            return { enrollmentId };
        });
    }
}

module.exports = CheckoutService;
