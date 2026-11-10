const express = require('express');
const { asyncHandler } = require('../middlewares/errorHandler');

module.exports = ({ reportController, requireAdmin }) => express.Router()
    .get('/api/admin/financial-report', requireAdmin, asyncHandler(reportController.financialReport));
