from django.db.models import Q

from .models import Brand, CartItem, Category, Product


def get_products(filters):
    queryset = Product.objects.all().select_related("brand", "category")

    # Filtering
    if filters.get("brand"):
        queryset = queryset.filter(brand=filters["brand"])
    if filters.get("category"):
        queryset = queryset.filter(category=filters["category"])
    if filters.get("in_stock") is not None:
        queryset = queryset.filter(
            in_stock=filters["in_stock"].lower() in ["true", "1"]
        )
    if filters.get("min_price"):
        queryset = queryset.filter(price__gte=filters["min_price"])
    if filters.get("max_price"):
        queryset = queryset.filter(price__lte=filters["max_price"])

    # Searching
    if filters.get("search"):
        search = filters["search"]
        queryset = queryset.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )

    # Ordering
    if filters.get("ordering"):
        queryset = queryset.order_by(filters["ordering"])

    return queryset


# Brand / category


def get_brands():
    return Brand.objects.all()


def get_categories():
    return Category.objects.all()


# cart items


# get cart items
def get_cart_items(request):
    if request.user.is_authenticated:
        return CartItem.objects.filter(user=request.user).select_related("product")
    else:
        if not request.session.session_key:
            request.session.create()
        return CartItem.objects.filter(
            session_id=request.session.session_key
        ).select_related("product")


def add_to_cart(request, product, quantity):
    if request.user.is_authenticated:
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={"quantity": quantity},
        )
    else:
        if not request.session.session_key:
            request.session.create()
        cart_item, created = CartItem.objects.get_or_create(
            session_id=request.session.session_key,
            product=product,
            defaults={"quantity": quantity},
        )
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    return cart_item


def update_cart_item(request, item_id, quantity):
    item = get_cart_items(request).get(pk=item_id)
    item.quantity = quantity
    item.save()
    return item


def delete_cart_item(request, item_id):
    item = get_cart_items(request).get(pk=item_id)
    item.delete()
    return True


def clear_cart(request):
    items = CartItem.objects.all()
    if request.user.is_authenticated:
        items = items.filter(user=request.user)
    else:
        items = items.filter(session_id=request.session.session_key)
    items.delete()
