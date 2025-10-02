import json

import stripe
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from . import service
from .Custom_response_helper import custom_response
from .models import CartItem, Product
from .serializers import (
    BrandSerializer,
    CartItemSerializer,
    CategorySerializer,
    ProductSerializer,
)


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 48

    def get_paginated_response(self, data):
        return Response(
            {
                "status_code": 200,
                "message": "Success",
                "data": {
                    "count": self.page.paginator.count,
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                    "results": data,
                },
            }
        )


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
            OpenApiParameter(
                "in_stock", bool, description="Filter by stock availability"
            ),
            OpenApiParameter("min_price", float, description="Filter by minimum price"),
            OpenApiParameter("max_price", float, description="Filter by maximum price"),
            OpenApiParameter(
                "search", str, description="Search in name or description"
            ),
            OpenApiParameter(
                "ordering", str, description="Order by price, rating, created_at"
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=ProductSerializer, description="List of products"
            ),
            400: OpenApiResponse(description="Bad Request"),  # bad request response
            403: OpenApiResponse(description="Permission Denied"),
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
            return custom_response(
                403,
                "Permission denied",
                errors={"detail": "Only admin users can add products."},
            )

        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            product = service.create_product(serializer.validated_data)
            return custom_response(
                201, "Product created successfully", ProductSerializer(product).data
            )
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
            200: OpenApiResponse(
                response=ProductSerializer, description="Product details"
            ),
            400: OpenApiResponse(description="Bad Request"),
            404: OpenApiResponse(description="Product not found"),
        },
    )
    def get(self, request, slug):
        try:
            product = service.get_product_by_slug(slug)
            serializer = ProductSerializer(product)
            return custom_response(
                200, "Product retrieved successfully", serializer.data
            )
        except:
            return custom_response(
                404,
                "Product not found",
                errors={"detail": "No product found with this slug."},
            )


# BRANDS/CATEGORIES


class BrandListView(APIView):
    permission_classes = [permissions.AllowAny]
    pagination_class = CustomPagination

    @extend_schema(
        summary="List all brands",
        description="Returns a list of all available brands.",
        responses={
            200: OpenApiResponse(
                response=BrandSerializer, description="List of brands"
            ),
            400: OpenApiResponse(description="Bad Request"),
            403: OpenApiResponse(description="Permission Denied"),
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
            200: OpenApiResponse(
                response=CategorySerializer, description="List of categories"
            ),
            400: OpenApiResponse(description="Bad Request"),
            403: OpenApiResponse(description="Permission Denied"),
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
        return custom_response(
            200, "Categories retrieved successfully", serializer.data
        )


# CART
class CartView(APIView):
    permission_classes = [permissions.AllowAny]

    def get_cart_queryset(self, request):
        if request.user.is_authenticated:
            return CartItem.objects.filter(user=request.user).select_related("product")
        else:
            session_id = request.session.session_key or request.session.save()
            return CartItem.objects.filter(
                session_id=request.session.session_key
            ).select_related("product")

    def get(self, request):
        items = service.get_cart_items(request)
        serializer = CartItemSerializer(items, many=True)
        return custom_response(
            200, "Cart items retrieved successfully", serializer.data
        )

    def post(self, request):
        serializer = CartItemSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.validated_data["product"]
            quantity = serializer.validated_data["quantity"]
            cart_item = service.add_to_cart(request, product, quantity)
            return custom_response(
                201,
                "Item added to cart successfully",
                CartItemSerializer(cart_item).data,
            )
        return custom_response(400, "Validation error", errors=serializer.errors)

    def patch(self, request):
        try:
            item = service.update_cart_item(
                request, request.data.get("id"), request.data.get("quantity")
            )
            return custom_response(
                200, "Cart item updated", CartItemSerializer(item).data
            )
        except:
            return custom_response(
                404, "Item not found", errors={"detail": "Cart item not found"}
            )

    def delete(self, request):
        try:
            service.delete_cart_item(request, request.data.get("id"))
            return custom_response(200, "Item removed from cart successfully")
        except:
            return custom_response(
                404, "Item not found", errors={"detail": "Cart item not found"}
            )


class CartClearView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        service.clear_cart(request)
        return Response({"message": "Cart cleared"}, status=status.HTTP_204_NO_CONTENT)


@csrf_exempt
def stripe_checkout_session(request, pk):
    request_data = json.loads(request.body)
    product = get_object_or_404(Product, pk=pk)

    quantity = int(request_data.get("quantity", 1))

    stripe.api_key = settings.STRIPE_SECRET_KEY
    checkout_session = stripe.checkout.Session.create(
        customer_email=request_data["email"],
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "pkr",
                    "product_data": {
                        "name": product.name,
                        "description": product.description,
                    },
                    "unit_amount": int(product.price * 100),
                },
                "quantity": quantity,
            }
        ],
        mode="payment",
        customer_creation="always",
        success_url=settings.PAYMENT_SUCCESS_URL,
        cancel_url=settings.PAYMENT_CANCEL_URL,
    )

    return JsonResponse({"sessionId": checkout_session.id, "url": checkout_session.url})


def payment_success(request):
    return render(request, "payment/success.html")


def payment_cancel(request):
    return render(request, "payment/cancel.html")


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return JsonResponse({"error": "Invalid payload"}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({"error": "Invalid signature"}, status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_email = session.get("customer_email")
        amount_total = session.get("amount_total")

        print(f"Payment successful for {customer_email}, Amount: {amount_total}")

    elif event["type"] == "payment_intent.payment_failed":
        intent = event["data"]["object"]
        print(f"Payment failed: {intent}")

    return JsonResponse({"status": "success"}, status=200)
