// Minimal structured logger with levels, replacing raw console.log calls
// scattered across the application. Swap the transport here (e.g. winston/pino)
// without touching call sites.
const { config } = require('./env');

function format(level, message, meta) {
    const entry = {
        level,
        message,
        timestamp: new Date().toISOString(),
        ...(meta ? { meta } : {}),
    };
    return JSON.stringify(entry);
}

const logger = {
    info(message, meta) {
        console.log(format('info', message, meta));
    },
    warn(message, meta) {
        console.warn(format('warn', message, meta));
    },
    error(message, meta) {
        console.error(format('error', message, meta));
    },
    debug(message, meta) {
        if (!config.isProduction) {
            console.debug(format('debug', message, meta));
        }
    },
};

module.exports = logger;
