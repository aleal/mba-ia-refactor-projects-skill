const config = Object.freeze({
    port: Number(process.env.PORT) || 3000,
    dbPath: process.env.DB_PATH || ':memory:',
    adminToken: process.env.ADMIN_TOKEN || '',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    logLevel: process.env.LOG_LEVEL || 'info',
});

module.exports = config;
