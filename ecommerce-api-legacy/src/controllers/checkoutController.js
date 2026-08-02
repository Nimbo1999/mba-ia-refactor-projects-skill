const { CheckoutError } = require('../services/checkoutService');

function isNonEmptyString(value) {
    return typeof value === 'string' && value.trim().length > 0;
}

// Orchestrates the HTTP flow for checkout: validates input, delegates to the
// service layer, and maps results/errors to HTTP responses. Contains no SQL
// and no business rules of its own.
class CheckoutController {
    constructor({ checkoutService }) {
        this.checkoutService = checkoutService;
        this.checkout = this.checkout.bind(this);
    }

    async checkout(req, res, next) {
        // External request contract (`usr`, `eml`, `pwd`, `c_id`, `card`) is
        // preserved for backward compatibility; mapped to descriptive names
        // for use in the rest of the flow.
        const { usr: username, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body;

        if (!isNonEmptyString(username) || !isNonEmptyString(email) ||
            (courseId === undefined || courseId === null) || !isNonEmptyString(cardNumber)) {
            return res.status(400).json({ erro: 'Bad Request', sucesso: false });
        }

        try {
            const { enrollmentId } = await this.checkoutService.checkout({
                username,
                email,
                password,
                courseId,
                cardNumber,
            });

            return res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
        } catch (err) {
            if (err instanceof CheckoutError) {
                return res.status(err.status).send(err.message);
            }
            return next(err);
        }
    }
}

module.exports = CheckoutController;
