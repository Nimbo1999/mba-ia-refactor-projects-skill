require('dotenv').config();

// Centralized configuration — every sensitive value comes from an environment
// variable, never a hardcoded literal. See .env.example for the expected keys.
const config = {
    port: Number(process.env.PORT) || 3000,
    nodeEnv: process.env.NODE_ENV || 'development',
    isProduction: process.env.NODE_ENV === 'production',
    dbUser: process.env.DB_USER,
    dbPassword: process.env.DB_PASSWORD,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    smtpUser: process.env.SMTP_USER,
    adminToken: process.env.ADMIN_TOKEN,
};

module.exports = { config };
