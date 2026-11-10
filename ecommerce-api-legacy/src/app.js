const config = require('./config');
const { openDatabase } = require('./database/connection');
const { createApp } = require('./server');
const { createLogger } = require('./utils/logger');

const logger = createLogger(config.logLevel);

async function main() {
    const db = await openDatabase(config.dbPath);
    const app = createApp({ db, config, logger });
    app.listen(config.port, () => logger.info(`LMS API rodando na porta ${config.port}`));
    if (!config.adminToken) logger.warn('ADMIN_TOKEN não definido: rotas administrativas bloqueadas.');
}

main().catch((err) => {
    logger.error('Falha ao iniciar a aplicação:', err);
    process.exit(1);
});
