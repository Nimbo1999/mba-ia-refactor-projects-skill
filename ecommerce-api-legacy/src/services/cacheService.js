// Encapsulated cache service instantiated once by the composition root and
// injected where needed, replacing the previous module-level mutable globals
// (`globalCache`, `totalRevenue`) that were imported directly by other modules.
const logger = require('../config/logger');

class CacheService {
    constructor() {
        this.store = new Map();
    }

    set(key, value) {
        logger.debug('Saving to cache', { key });
        this.store.set(key, value);
    }

    get(key) {
        return this.store.get(key);
    }
}

module.exports = CacheService;
