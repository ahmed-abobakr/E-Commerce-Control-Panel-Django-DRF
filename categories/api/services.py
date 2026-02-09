from categories.models import Category


def list_categories():
    """
        return all categories
    """
    result = Category.objects.all()
    print(f"get all Categories Data: {result}")
    return result


def get_category(category_id):
    """
        return category with id = category_id
    """
    result = Category.objects.filter(id=category_id).first()
    print(f"get category with id = {category_id}: {result}")
    return result
