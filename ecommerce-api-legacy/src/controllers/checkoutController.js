const { AppError } = require('../middlewares/errorHandler');

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+$/;

const isNonEmptyString = (value) => typeof value === 'string' && value.trim() !== '';

function parseCheckout(body) {
    const { usr: name, eml: email, pwd: password, c_id: courseId, card: cardNumber } = body ?? {};
    const valid = isNonEmptyString(name)
        && isNonEmptyString(email) && EMAIL_PATTERN.test(email)
        && courseId !== undefined && courseId !== null && courseId !== ''
        && isNonEmptyString(cardNumber)
        && (password === undefined || password === null || typeof password === 'string');
    if (!valid) throw new AppError('Bad Request', 400);
    return { name, email, password, courseId, cardNumber };
}

class CheckoutController {
    constructor({ checkoutService }) {
        this.checkoutService = checkoutService;
    }

    checkout = async (req, res) => {
        const { enrollmentId } = await this.checkoutService.checkout(parseCheckout(req.body));
        res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
    };
}

module.exports = CheckoutController;
