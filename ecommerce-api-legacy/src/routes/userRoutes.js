const express = require('express');
const { asyncHandler } = require('../middlewares/errorHandler');

module.exports = ({ userController, requireAdmin }) => express.Router()
    .delete('/api/users/:id', requireAdmin, asyncHandler(userController.remove));
