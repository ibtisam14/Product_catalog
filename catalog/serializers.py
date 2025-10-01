from rest_framework import serializers

from .models import Brand, CartItem, Category, Product


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name", "slug"]

    def validate_name(self, value):
        """Ensure brand name is unique (API-friendly error message)."""
        if Brand.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Brand with this name already exists.")
        return value


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]

    def validate_name(self, value):
        """Ensure category name is unique (API-friendly error message)."""
        if Category.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Category with this name already exists.")
        return value


class ProductSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True)
    category = CategorySerializer(read_only=True)

    brand_id = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(), source="brand", write_only=True
    )
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source="category", write_only=True
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "brand",
            "category",
            "brand_id",
            "category_id",
            "description",
            "price",
            "rating",
            "in_stock",
            "image_url",
            "created_at",
            "updated_at",
        ]

    # ---- FIELD LEVEL VALIDATIONS ----
    def validate_price(self, value):
        """Price must always be >= 0.01"""
        if value < 0.01:
            raise serializers.ValidationError("Price must be at least 0.01.")
        return value

    def validate_rating(self, value):
        """Rating must be between 0 and 5"""
        if value < 0 or value > 5:
            raise serializers.ValidationError("Rating must be between 0 and 5.")
        return value

    # ---- OBJECT LEVEL VALIDATIONS ----
    def validate(self, data):
        """
        Extra business rule checks.
        Example: Disallow product creation if marked in_stock=False but still has a price.
        """
        if not data.get("in_stock", True) and data.get("price", 0) > 0:
            raise serializers.ValidationError(
                {"in_stock": "Out-of-stock products should not have a price."}
            )
        return data


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product", write_only=True
    )

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_id", "quantity", "added_at"]

    # ---- FIELD LEVEL VALIDATIONS ----
    def validate_quantity(self, value):
        """Quantity must always be >= 1"""
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value

    # ---- OBJECT LEVEL VALIDATIONS ----
    def validate(self, data):
        """Check product stock before adding to cart"""
        product = data.get("product")
        if product and not product.in_stock:
            raise serializers.ValidationError(
                {"product": f"Product '{product.name}' is out of stock."}
            )
        return data
