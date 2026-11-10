class ReportController {
    constructor({ reports }) {
        this.reports = reports;
    }

    financialReport = async (req, res) => {
        res.json(await this.reports.financialReport());
    };
}

module.exports = ReportController;
