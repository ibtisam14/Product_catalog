from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework.pagination import PageNumberPagination 
from .models import Brand, Category, Product, CartItem
from .Custom_response_helper import custom_response
from . import service
from .serializers import BrandSerializer, CategorySerializer, ProductSerializer, CartItemSerializer


# ADD THIS CUSTOM PAGINATION CLASS RIGHT HERE
class CustomPagination(PageNumberPagination):
    page_size = 10 
    page_size_query_param = "page_size"
    max_page_size = 48 

    def get_paginated_response(self, data):
        return Response({
            "status_code": 200,
            "message": "Success",
            "data": {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data
            }
        })

# PRODUCTS 

class ProductListView(APIView):
    permission_classes = [permissions.AllowAny]  
    pagination_class = CustomPagination 
    @extend_schema(
        summary="List all products",
        description="Returns a list of products with filtering, searching, and ordering.",
        parameters=[
            OpenApiParameter("brand", str, description="Filter by brand ID"),
            OpenApiParameter("category", str, description="Filter by category ID"),
            OpenApiParameter("in_stock", bool, description="Filter by stock availability"),
            OpenApiParameter("min_price", float, description="Filter by minimum price"),
            OpenApiParameter("max_price", float, description="Filter by maximum price"),
            OpenApiParameter("search", str, description="Search in name or description"),
            OpenApiParameter("ordering", str, description="Order by price, rating, created_at"),
        ],
        responses={
            200: OpenApiResponse(response=ProductSerializer, description="List of products"),
            400: OpenApiResponse(description="Bad Request"),
        },
    )
    
    
    def get(self, request):
        queryset = service.get_products(request.query_params) 
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = ProductSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = ProductSerializer(queryset, many=True)
        return custom_response(200, "Products retrieved successfully", serializer.data)
    
    
    
    def post(self, request):
        if not request.user.is_authenticated or not request.user.is_staff:
            return custom_response(403, "Permission denied", errors={"detail": "Only admin users can add products."})

        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            product = service.create_product(serializer.validated_data)  
            return custom_response(201, "Product created successfully", ProductSerializer(product).data)
        return custom_response(400, "Validation error", errors=serializer.errors)   
class ProductDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Retrieve product details",
        description="Fetch product details by slug.",
        parameters=[
            OpenApiParameter("slug", str, description="Unique slug of the product"),
        ],
        responses={
            200: OpenApiResponse(response=ProductSerializer, description="Product details"),
            404: OpenApiResponse(description="Product not found"),
        },
    )
    
    
    
    def get(self, request, slug):
        try:
            product = service.get_product_by_slug(slug) 
            serializer = ProductSerializer(product)
            return custom_response(200, "Product retrieved successfully", serializer.data)
        except:
            return custom_response(404, "Product not found", errors={"detail": "No product found with this slug."})
# BRANDS/CATEGORIES 

class BrandListView(APIView):
    permission_classes = [permissions.AllowAny]
    pagination_class = CustomPagination 

    @extend_schema(
        summary="List all brands",
        description="Returns a list of all available brands.",
        responses={
            200: OpenApiResponse(response=BrandSerializer, description="List of brands"),
            400: OpenApiResponse(description="Bad Request"),
        },
    )
    def get(self, request):
        queryset = service.get_brands()  
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = BrandSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = BrandSerializer(queryset, many=True)
        return custom_response(200, "Brands retrieved successfully", serializer.data)


class CategoryListView(APIView):
    permission_classes = [permissions.AllowAny]
    pagination_class = CustomPagination 

    @extend_schema(
        summary="List all categories",
        description="Returns a list of all available categories.",
        responses={
            200: OpenApiResponse(response=CategorySerializer, description="List of categories"),
            400: OpenApiResponse(description="Bad Request"),
        },
    ) 
    
    
    

    def get(self, request):
        queryset = service.get_categories()  
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = CategorySerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = CategorySerializer(queryset, many=True)
        return custom_response(200, "Categories retrieved successfully", serializer.data)

# --------- CART ----------
class CartView(APIView):
    def get_cart_queryset(self, request):
        if request.user.is_authenticated:
            return CartItem.objects.filter(user=request.user).select_related("product")
        else:
            session_id = request.session.session_key or request.session.save()
            return CartItem.objects.filter(session_id=request.session.session_key).select_related("product")

    def get(self, request):
        items = service.get_cart_items(request) 
        serializer = CartItemSerializer(items, many=True)
        return custom_response(200, "Cart items retrieved successfully", serializer.data)

    def post(self, request):
        serializer = CartItemSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.validated_data["product"]
            quantity = serializer.validated_data["quantity"]
            cart_item = service.add_to_cart(request, product, quantity) 
            return custom_response(201, "Item added to cart successfully", CartItemSerializer(cart_item).data)
        return custom_response(400, "Validation error", errors=serializer.errors) 
    
    
    def patch(self, request):
        try:
            item = service.update_cart_item(request, request.data.get("id"), request.data.get("quantity"))
            return custom_response(200, "Cart item updated", CartItemSerializer(item).data)
        except:
            return custom_response(404, "Item not found", errors={"detail": "Cart item not found"})
    
    
    def delete(self, request):
        try:
            service.delete_cart_item(request, request.data.get("id"))  
            return custom_response(200, "Item removed from cart successfully")
        except:
            return custom_response(404, "Item not found", errors={"detail": "Cart item not found"}) 


class CartClearView(APIView):
    def post(self, request):
        service.clear_cart(request)  
        return Response({"message": "Cart cleared"}, status=status.HTTP_204_NO_CONTENT)
