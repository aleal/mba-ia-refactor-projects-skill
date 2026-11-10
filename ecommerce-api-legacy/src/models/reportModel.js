const { PAYMENT_STATUS, UNKNOWN_STUDENT } = require('../config/constants');

class ReportModel {
    constructor(db) { this.db = db; }

    // Uma única query (antes: 1 + cursos + 2 × matrículas).
    async financialReport() {
        const rows = await this.db.all(`
            SELECT c.id AS course_id, c.title, e.id AS enrollment_id,
                   u.name AS student, p.amount, p.status
            FROM courses c
            LEFT JOIN enrollments e ON e.course_id = c.id
            LEFT JOIN users u ON u.id = e.user_id
            LEFT JOIN payments p ON p.enrollment_id = e.id
            ORDER BY c.id, e.id`);

        const byCourse = new Map();
        for (const row of rows) {
            if (!byCourse.has(row.course_id)) {
                byCourse.set(row.course_id, { course: row.title, revenue: 0, students: [] });
            }
            if (row.enrollment_id === null) continue;

            const entry = byCourse.get(row.course_id);
            if (row.status === PAYMENT_STATUS.PAID) entry.revenue += row.amount;
            entry.students.push({ student: row.student ?? UNKNOWN_STUDENT, paid: row.amount ?? 0 });
        }
        return [...byCourse.values()];
    }
}

module.exports = ReportModel;
