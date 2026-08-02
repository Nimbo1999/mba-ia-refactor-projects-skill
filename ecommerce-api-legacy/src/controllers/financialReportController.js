// Orchestrates the HTTP flow for the admin financial report.
class FinancialReportController {
    constructor({ financialReportService }) {
        this.financialReportService = financialReportService;
        this.getReport = this.getReport.bind(this);
    }

    async getReport(req, res, next) {
        try {
            const report = await this.financialReportService.buildReport();
            return res.json(report);
        } catch (err) {
            return next(err);
        }
    }
}

module.exports = FinancialReportController;
