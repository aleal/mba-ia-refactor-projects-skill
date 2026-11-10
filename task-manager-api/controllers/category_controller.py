from controllers.validators import validate_category_changes, validate_new_category
from middlewares.error_handler import NotFoundError
from models.category import Category


class CategoryController:
    def list_categories(self):
        result = []
        for category, task_count in Category.list_with_task_counts():
            data = category.to_dict()
            data['task_count'] = task_count
            result.append(data)
        return result, 200

    def create_category(self, data):
        category = Category(**validate_new_category(data)).save()
        return category.to_dict(), 201

    def update_category(self, category_id, data):
        category = self._get_or_404(category_id)
        for field, value in validate_category_changes(data).items():
            setattr(category, field, value)
        category.save()
        return category.to_dict(), 200

    def delete_category(self, category_id):
        # As tasks da categoria ficam com category_id = NULL (relacionamento sem cascade de delete).
        self._get_or_404(category_id).delete()
        return {'message': 'Categoria deletada'}, 200

    @staticmethod
    def _get_or_404(category_id):
        category = Category.get_by_id(category_id)
        if category is None:
            raise NotFoundError('Categoria não encontrada')
        return category
