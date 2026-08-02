const { Router } = require('express');
const { requireAdmin } = require('../middlewares/authMiddleware');

module.exports = function userRoutes(userController) {
  const router = Router();
  router.delete('/users/:id', requireAdmin, userController.deleteUser);
  return router;
};
