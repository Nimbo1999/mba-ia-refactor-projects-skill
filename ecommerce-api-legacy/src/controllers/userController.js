// Orchestrates the HTTP flow for deleting a user.
class UserController {
    constructor({ userService }) {
        this.userService = userService;
        this.deleteUser = this.deleteUser.bind(this);
    }

    async deleteUser(req, res, next) {
        const { id } = req.params;

        try {
            await this.userService.deleteUser(id);
            // Response updated to reflect the fix: enrollments/payments are now
            // cleaned up in cascade instead of being left orphaned.
            return res.send('Usuário e seus dados relacionados foram deletados com sucesso.');
        } catch (err) {
            return next(err);
        }
    }
}

module.exports = UserController;
