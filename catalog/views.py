from rest_framework import generics, viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from .models import Brand, Category, Product, CartItem
from .serializers import BrandSerializer, CategorySerializer, ProductSerializer, CartItemSerializer


# --------- PRODUCTS ----------
class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all().select_related("brand", "category")
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["brand", "category", "in_stock"]
    search_fields = ["name", "description"]
    ordering_fields = ["price", "rating", "created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        # Filtering by price range (min_price, max_price)
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)
        return qs


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all().select_related("brand", "category")
    serializer_class = ProductSerializer
    lookup_field = "slug"


# --------- BRANDS / CATEGORIES ----------
class BrandListView(generics.ListAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


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
