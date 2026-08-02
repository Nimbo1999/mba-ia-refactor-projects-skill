const { Router } = require('express');
const { requireAdmin } = require('../middlewares/authMiddleware');

module.exports = function adminRoutes(financialReportController) {
  const router = Router();
  router.get('/admin/financial-report', requireAdmin, financialReportController.getReport);
  return router;
};
