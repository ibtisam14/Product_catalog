  # import django modules and models  
from django.db.models import Q   # Q object for complex queries
from .models import Product, Brand, Category, CartItem # import models that in present in models.py

def get_products(filters):   # get function to get products with filters
    queryset = Product.objects.all().select_related("brand", "category") # select related to optimize queries

    # Filtering
    if filters.get("brand"):   # filter by brand
        queryset = queryset.filter(brand=filters["brand"]) # select specific brand if call
    if filters.get("category"):  # filter by category
        queryset = queryset.filter(category=filters["category"])  # select specific category if call
    if filters.get("in_stock") is not None: # filter by stock availability
        queryset = queryset.filter(in_stock=filters["in_stock"].lower() in ["true", "1"]) # select specific stock availability if call and then convert to boolean
    if filters.get("min_price"):  # filter by minimum price (gte means greater than or equal to)
        queryset = queryset.filter(price__gte=filters["min_price"]) # select specific minimum price if call
    if filters.get("max_price"): # filter by maximum price (lte means less than or equal to)
        queryset = queryset.filter(price__lte=filters["max_price"]) # select specific maximum price if call

    # Searching
    if filters.get("search"):
        search = filters["search"] #search term
         # filter by name or description (icontains means case-insensitive contains)
        queryset = queryset.filter(Q(name__icontains=search) | Q(description__icontains=search))

    # Ordering
    if filters.get("ordering"): # order by field
        queryset = queryset.order_by(filters["ordering"]) # order by specific field if call

    return queryset  # return the final queryset that is filtered, searched, and ordered


   # Brand / category     
   
     
def get_brands():  # return all brands from database 
    return Brand.objects.all()



def get_categories():  # return all categories from database
    return Category.objects.all()  


# cart items 

#get cart items
def get_cart_items(request):    #get cart items based on user authentication
    if request.user.is_authenticated:  # if user is authenticated
        return CartItem.objects.filter(user=request.user).select_related("product") # select related to optimize queries
    else:
        if not request.session.session_key: # for anonymous users, create a session if not exists
            request.session.create() # create session
        return CartItem.objects.filter(session_id=request.session.session_key).select_related("product") #return cart item with session id 
    


def add_to_cart(request, product, quantity): # add item to cart based on user authentication
    if request.user.is_authenticated: # if user is authenticated
        cart_item, created = CartItem.objects.get_or_create( # get or create cart item
            user=request.user, product=product, defaults={"quantity": quantity} # if not exists, create with default quantity
        )
    else:
        if not request.session.session_key: # for anonymous users, create a session if not exists
            request.session.create() # create session
        cart_item, created = CartItem.objects.get_or_create( # get or create cart item
            session_id=request.session.session_key, product=product, defaults={"quantity": quantity} # if not exists, create with default quantity
        )
    if not created: # if cart item already exists, update quantity
        cart_item.quantity += quantity # add quantity
        cart_item.save() # save cart item
    return cart_item # return cart item


def update_cart_item(request, item_id, quantity): # update cart item quantity based on user authentication
    item = get_cart_items(request).get(pk=item_id) # get cart item by id
    item.quantity = quantity # update quantity
    item.save() # save cart item
    return item # return cart item


def delete_cart_item(request, item_id): # delete cart item based on user authentication
    item = get_cart_items(request).get(pk=item_id) # get cart item by id
    item.delete() # delete cart item
    return True # return true if deleted


def clear_cart(request): # clear all cart items based on user authentication
    items = CartItem.objects.all() # get all cart items
    if request.user.is_authenticated: # if user is authenticated
        items = items.filter(user=request.user) # filter by user
    else:
        items = items.filter(session_id=request.session.session_key) # filter by session id
    items.delete()     # delete all cart items