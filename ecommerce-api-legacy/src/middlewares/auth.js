const crypto = require('node:crypto');
const { AppError } = require('./errorHandler');

// Sem ADMIN_TOKEN configurado, as rotas protegidas ficam sempre bloqueadas.
function requireAdmin(config) {
    const expected = Buffer.from(config.adminToken);
    return (req, res, next) => {
        const header = req.get('X-Admin-Token');
        if (!header) return next(new AppError('Não autorizado', 401));

        const provided = Buffer.from(header);
        const valid = expected.length > 0
            && provided.length === expected.length
            && crypto.timingSafeEqual(provided, expected);
        return valid ? next() : next(new AppError('Acesso negado', 403));
    };
}

module.exports = { requireAdmin };
