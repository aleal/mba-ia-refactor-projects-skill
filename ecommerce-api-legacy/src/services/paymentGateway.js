const { PAYMENT_STATUS, APPROVED_CARD_PREFIX } = require('../config/constants');

// Gateway simulado. Uma integração real entra aqui sem tocar no checkout.
class PaymentGateway {
    constructor({ apiKey, logger }) {
        this.apiKey = apiKey;
        this.logger = logger;
    }

    charge(cardNumber, amount) {
        this.logger.info(`Processando pagamento de ${amount} no cartão final ${cardNumber.slice(-4)}`);
        return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
    }
}

module.exports = PaymentGateway;
