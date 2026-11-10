class AppError extends Error {
    constructor(message, status = 400) {
        super(message);
        this.status = status;
    }
}

const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

// Erros em texto puro, como a API sempre respondeu.
function createErrorHandler(logger) {
    return (err, req, res, next) => {
        if (err instanceof AppError) return res.status(err.status).send(err.message);
        if (err.type === 'entity.parse.failed') return res.status(400).send('Bad Request');
        logger.error(`${req.method} ${req.originalUrl} falhou:`, err);
        return res.status(500).send('Erro interno');
    };
}

module.exports = { AppError, asyncHandler, createErrorHandler };
