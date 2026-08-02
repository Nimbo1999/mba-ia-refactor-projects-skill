const logger = require('../config/logger');
const { config } = require('../config/env');

// Single centralized point for translating thrown/propagated errors into a
// consistent HTTP response, avoiding stack-trace leakage in production.
function errorHandler(err, req, res, next) { // eslint-disable-line no-unused-vars
    const status = err.status || 500;

    logger.error('Unhandled request error', {
        message: err.message,
        path: req.path,
        ...(config.isProduction ? {} : { stack: err.stack }),
    });

    res.status(status).json({
        erro: status === 500 ? 'Erro interno do servidor' : err.message,
        sucesso: false,
    });
}

module.exports = errorHandler;
