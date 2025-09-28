from rest_framework import generics, viewsets, mixins, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from .models import Brand, Category, Product, CartItem
from .serializers import BrandSerializer, CategorySerializer, ProductSerializer, CartItemSerializer

# --------- PRODUCTS ----------

class ProductListView(APIView):
    permission_classes = [permissions.AllowAny]  # Change to IsAuthenticated if needed

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
        queryset = Product.objects.all().select_related("brand", "category")

        # Filtering
        brand = request.query_params.get("brand")
        category = request.query_params.get("category")
        in_stock = request.query_params.get("in_stock")
        min_price = request.query_params.get("min_price")
        max_price = request.query_params.get("max_price")

        if brand:
            queryset = queryset.filter(brand=brand)
        if category:
            queryset = queryset.filter(category=category)
        if in_stock is not None:
            queryset = queryset.filter(in_stock=in_stock.lower() in ["true", "1"])
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # Searching
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                name__icontains=search
            ) | queryset.filter(description__icontains=search)

        # Ordering
        ordering = request.query_params.get("ordering")
        if ordering:
            queryset = queryset.order_by(ordering)

        serializer = ProductSerializer(queryset, many=True)
        return Response(
            {"count": len(serializer.data), "results": serializer.data},
            status=status.HTTP_200_OK,
        )


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
        product = get_object_or_404(
            Product.objects.select_related("brand", "category"),
            slug=slug,
        )
        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)

# --------- BRANDS / CATEGORIES ----------

class BrandListView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="List all brands",
        description="Returns a list of all available brands.",
        responses={
            200: OpenApiResponse(response=BrandSerializer, description="List of brands"),
            400: OpenApiResponse(description="Bad Request"),
        },
    )
    def get(self, request):
        queryset = Brand.objects.all()
        serializer = BrandSerializer(queryset, many=True)
        return Response(
            {
                "count": len(serializer.data),
                "results": serializer.data
            },
            status=status.HTTP_200_OK,
        )



class CategoryListView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="List all categories",
        description="Returns a list of all available categories.",
        responses={
            200: OpenApiResponse(response=CategorySerializer, description="List of categories"),
            400: OpenApiResponse(description="Bad Request"),
        },
    )
    def get(self, request):
        queryset = Category.objects.all()
        serializer = CategorySerializer(queryset, many=True)
        return Response(
            {
                "count": len(serializer.data),
                "results": serializer.data
            },
            status=status.HTTP_200_OK,
        )

# --------- CART ----------
class CartView(APIView):
    def get_cart_queryset(self, request):
        if request.user.is_authenticated:
            return CartItem.objects.filter(user=request.user).select_related("product")
        else:
            session_id = request.session.session_key or request.session.save()
            return CartItem.objects.filter(session_id=request.session.session_key).select_related("product")

    def get(self, request):
        items = self.get_cart_queryset(request)
        serializer = CartItemSerializer(items, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CartItemSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.validated_data["product"]
            quantity = serializer.validated_data["quantity"]

            if request.user.is_authenticated:
                cart_item, created = CartItem.objects.get_or_create(
                    user=request.user, product=product, defaults={"quantity": quantity}
                )
            else:
                if not request.session.session_key:
                    request.session.create()
                cart_item, created = CartItem.objects.get_or_create(
                    session_id=request.session.session_key, product=product, defaults={"quantity": quantity}
                )
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            return Response(CartItemSerializer(cart_item).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk=None):
        try:
            item = self.get_cart_queryset(request).get(pk=request.data.get("id"))
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)

        item.quantity = request.data.get("quantity", item.quantity)
        item.save()
        return Response(CartItemSerializer(item).data)

    def delete(self, request):
        try:
            item = self.get_cart_queryset(request).get(pk=request.data.get("id"))
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)


class CartClearView(APIView):
    def post(self, request):
        items = CartItem.objects.all()
        if request.user.is_authenticated:
            items = items.filter(user=request.user)
        else:
            items = items.filter(session_id=request.session.session_key)
        items.delete()
        return Response({"message": "Cart cleared"}, status=status.HTTP_204_NO_CONTENT)
