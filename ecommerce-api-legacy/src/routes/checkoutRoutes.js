const { Router } = require('express');

module.exports = function checkoutRoutes(checkoutController) {
    const router = Router();
    router.post('/checkout', checkoutController.checkout);
    return router;
};
