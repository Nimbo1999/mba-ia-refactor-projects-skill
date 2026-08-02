// Builds the admin financial report from a single joined query result,
// aggregating in memory instead of issuing a query per course/enrollment.
class FinancialReportService {
    constructor({ enrollmentModel }) {
        this.enrollmentModel = enrollmentModel;
    }

    async buildReport() {
        const rows = await this.enrollmentModel.findReportRows();

        const coursesById = new Map();

        for (const row of rows) {
            if (!coursesById.has(row.course_id)) {
                coursesById.set(row.course_id, {
                    course: row.course_title,
                    revenue: 0,
                    students: [],
                });
            }

            const courseData = coursesById.get(row.course_id);

            if (!row.enrollment_id) {
                continue; // course with no enrollments
            }

            if (row.payment_status === 'PAID') {
                courseData.revenue += row.payment_amount;
            }

            courseData.students.push({
                student: row.student_name || 'Unknown',
                paid: row.payment_amount || 0,
            });
        }

        return Array.from(coursesById.values());
    }
}

module.exports = FinancialReportService;
