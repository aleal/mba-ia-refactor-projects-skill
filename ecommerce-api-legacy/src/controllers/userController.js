const { AppError } = require('../middlewares/errorHandler');

class UserController {
    constructor({ users }) {
        this.users = users;
    }

    // Mantém 200 mesmo quando o id não existe, como a API original.
    remove = async (req, res) => {
        const id = Number(req.params.id);
        if (!Number.isInteger(id) || id <= 0) throw new AppError('Bad Request', 400);
        await this.users.remove(id);
        res.send('Usuário deletado, junto com suas matrículas e pagamentos.');
    };
}

module.exports = UserController;
