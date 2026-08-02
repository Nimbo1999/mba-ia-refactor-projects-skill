const { config } = require('../config/env');

// Minimal admin authentication: requires a bearer token matching ADMIN_TOKEN.
// Protects the destructive/sensitive endpoints that previously had no
// authentication at all.
function requireAdmin(req, res, next) {
    const authHeader = req.get('authorization') || '';
    const [, token] = authHeader.split(' ');

    if (!config.adminToken || token !== config.adminToken) {
        return res.status(401).json({ erro: 'Não autorizado', sucesso: false });
    }

    return next();
}

module.exports = { requireAdmin };
