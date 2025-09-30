from rest_framework import status, permissions # for permission classes and status codes 
from rest_framework.response import Response # for returning responses
from rest_framework.views import APIView # for creating API views
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse # for API documentation
from rest_framework.pagination import PageNumberPagination  # for pagination
from .models import CartItem # import models
from .Custom_response_helper import custom_response # import custom response helper
from . import service # import service module
from .serializers import BrandSerializer, CategorySerializer, ProductSerializer, CartItemSerializer # import serializers


# ADD THIS CUSTOM PAGINATION CLASS 
class CustomPagination(PageNumberPagination): # custom pagination class
    page_size = 10  # default page size
    page_size_query_param = "page_size" # allow client to set page size
    max_page_size = 48  # maximum page size

    def get_paginated_response(self, data): # custom paginated response
        return Response({ # custom response format
            "status_code": 200,
            "message": "Success",
            "data": {
                "count": self.page.paginator.count, # total items
                "next": self.get_next_link(), # next page link
                "previous": self.get_previous_link(), # previous page link
                "results": data # paginated data
            }
        })

# PRODUCTS 

class ProductListView(APIView):   # product list view with filtering, searching, ordering, and pagination
    permission_classes = [permissions.AllowAny]  # allow any user to access
    pagination_class = CustomPagination  # use custom pagination class
    @extend_schema( # API documentation
        summary="List all products", # summary of the endpoint
        description="Returns a list of products with filtering, searching, and ordering.", # description of the endpoint
        parameters=[ # parameters for filtering, searching, and ordering
            OpenApiParameter("brand", str, description="Filter by brand ID"), # brand filter parameter
            OpenApiParameter("category", str, description="Filter by category ID"), # category filter parameter
            OpenApiParameter("in_stock", bool, description="Filter by stock availability"), # stock availability filter parameter
            OpenApiParameter("min_price", float, description="Filter by minimum price"), # minimum price filter parameter
            OpenApiParameter("max_price", float, description="Filter by maximum price"), # maximum price filter parameter
            OpenApiParameter("search", str, description="Search in name or description"), # search parameter
            OpenApiParameter("ordering", str, description="Order by price, rating, created_at"), # ordering parameter
        ],
        responses={ # API responses
            200: OpenApiResponse(response=ProductSerializer, description="List of products"), # successful response
            400: OpenApiResponse(description="Bad Request"), # bad request response
            403: OpenApiResponse(description="Permission Denied"), # permission denied response
        },
    )
    
    
    def get(self, request): # get method for listing products
        queryset = service.get_products(request.query_params)  # get products with filters from query parameters
        paginator = self.pagination_class() # instantiate pagination class
        page = paginator.paginate_queryset(queryset, request) # paginate the queryset
        if page is not None: # if there is a page
            serializer = ProductSerializer(page, many=True) # serialize the page
            return paginator.get_paginated_response(serializer.data) # return paginated response

        serializer = ProductSerializer(queryset, many=True) # serialize the entire queryset
        return custom_response(200, "Products retrieved successfully", serializer.data) # return custom response
    
    
    
    def post(self, request): # post method for creating a new product
        if not request.user.is_authenticated or not request.user.is_staff: # check if user is authenticated and is admin
            return custom_response(403, "Permission denied", errors={"detail": "Only admin users can add products."}) # return permission denied response

        serializer = ProductSerializer(data=request.data) # serialize the request data
        if serializer.is_valid(): # if serializer is valid
            product = service.create_product(serializer.validated_data) # create product with validated data  
            return custom_response(201, "Product created successfully", ProductSerializer(product).data) # return custom response with created product
        return custom_response(400, "Validation error", errors=serializer.errors)   # return custom response with validation errors
class ProductDetailView(APIView): # product detail view with slug
    permission_classes = [permissions.AllowAny] # allow any user to access

    @extend_schema( # API documentation
        summary="Retrieve product details", # summary of the endpoint
        description="Fetch product details by slug.", # description of the endpoint
        parameters=[ # parameters for the endpoint
            OpenApiParameter("slug", str, description="Unique slug of the product"), # slug parameter
        ],
        responses={ # API responses
            200: OpenApiResponse(response=ProductSerializer, description="Product details"), # successful response
            400: OpenApiResponse(description="Bad Request"), # bad request response
            404: OpenApiResponse(description="Product not found"), # product not found response 
        },
    )
    
    
    
    def get(self, request, slug): # get method for retrieving product details by slug
        try:
            product = service.get_product_by_slug(slug)     # get product by slug
            serializer = ProductSerializer(product) # serialize the product
            return custom_response(200, "Product retrieved successfully", serializer.data) # return custom response with product details
        except:
            return custom_response(404, "Product not found", errors={"detail": "No product found with this slug."}) # return custom response if product not found
# BRANDS/CATEGORIES 

class BrandListView(APIView): # brand list view with pagination
    permission_classes = [permissions.AllowAny] # allow any user to access
    pagination_class = CustomPagination         # use custom pagination class

    @extend_schema(    # API documentation
        summary="List all brands", # summary of the endpoint
        description="Returns a list of all available brands.", # description of the endpoint
        responses={ # API responses
            200: OpenApiResponse(response=BrandSerializer, description="List of brands"), # successful response
            400: OpenApiResponse(description="Bad Request"), # bad request response
            403: OpenApiResponse(description="Permission Denied"), # permission denied response
        },
    )
    def get(self, request): # get method for listing brands
        queryset = service.get_brands()  # get all brands from service
        paginator = self.pagination_class() # instantiate pagination class
        page = paginator.paginate_queryset(queryset, request) # paginate the queryset
        if page is not None:
            serializer = BrandSerializer(page, many=True) # serialize the page
            return paginator.get_paginated_response(serializer.data) # return paginated response

        serializer = BrandSerializer(queryset, many=True) # serialize the entire queryset
        return custom_response(200, "Brands retrieved successfully", serializer.data) # return custom response


class CategoryListView(APIView):  # category list view with pagination
    permission_classes = [permissions.AllowAny] # allow any user to access
    pagination_class = CustomPagination  # use custom pagination class

    @extend_schema( # API documentation
        summary="List all categories",# summary of the endpoint
        description="Returns a list of all available categories.", # description of the endpoint
        responses={ # API responses
            200: OpenApiResponse(response=CategorySerializer, description="List of categories"), # successful response
            400: OpenApiResponse(description="Bad Request"), # bad request response
            403: OpenApiResponse(description="Permission Denied"), # permission denied response
        },
    ) 
    
    
    

    def get(self, request): # get method for listing categories
        queryset = service.get_categories()  # get all categories from service 
        paginator = self.pagination_class() # instantiate pagination class
        page = paginator.paginate_queryset(queryset, request) # paginate the queryset
        if page is not None: # if there is a page
            serializer = CategorySerializer(page, many=True) # serialize the page
            return paginator.get_paginated_response(serializer.data) # return paginated response

        serializer = CategorySerializer(queryset, many=True) # serialize the entire queryset
        return custom_response(200, "Categories retrieved successfully", serializer.data) # return custom response

# --------- CART ----------
class CartView(APIView): # cart view for managing cart items
    permission_classes = [permissions.AllowAny] # allow any user to access
    def get_cart_queryset(self, request): # get cart items based on user authentication
        if request.user.is_authenticated: # if user is authenticated
            return CartItem.objects.filter(user=request.user).select_related("product") # select related to optimize queries
        else:
            session_id = request.session.session_key or request.session.save() # ensure session exists
            return CartItem.objects.filter(session_id=request.session.session_key).select_related("product") #return cart item with session id

    def get(self, request): # get method for retrieving cart items
        items = service.get_cart_items(request)  # get cart items from service
        serializer = CartItemSerializer(items, many=True) # serialize the cart items
        return custom_response(200, "Cart items retrieved successfully", serializer.data) # return custom response with cart items

    def post(self, request): # post method for adding item to cart
        serializer = CartItemSerializer(data=request.data) # serialize the request data
        if serializer.is_valid(): # if serializer is valid
            product = serializer.validated_data["product"] # get product from validated data
            quantity = serializer.validated_data["quantity"] # get quantity from validated data
            cart_item = service.add_to_cart(request, product, quantity)  # add item to cart using service
            return custom_response(201, "Item added to cart successfully", CartItemSerializer(cart_item).data) # return custom response with cart item
        return custom_response(400, "Validation error", errors=serializer.errors)  # return custom response with validation errors
    
    
    def patch(self, request):
        try:
            item = service.update_cart_item(request, request.data.get("id"), request.data.get("quantity"))
            return custom_response(200, "Cart item updated", CartItemSerializer(item).data)
        except:
            return custom_response(404, "Item not found", errors={"detail": "Cart item not found"})
    
    
    def delete(self, request): # delete method for removing item from cart
        try:
            service.delete_cart_item(request, request.data.get("id"))   # delete cart item using service
            return custom_response(200, "Item removed from cart successfully") # return custom response if item removed
        except:
            return custom_response(404, "Item not found", errors={"detail": "Cart item not found"}) # return custom response if item not found


class CartClearView(APIView):  # cart clear view for clearing all cart items
    permission_classes = [permissions.AllowAny] # allow any user to access
    def post(self, request): # post method for clearing cart
        service.clear_cart(request)   # clear cart using service
        return Response({"message": "Cart cleared"}, status=status.HTTP_204_NO_CONTENT) # return response if cart cleared
