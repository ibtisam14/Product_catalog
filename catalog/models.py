from decimal import Decimal
from django.conf import settings
from django.db import models
from django.db.models import Q, Index, UniqueConstraint
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator


def generate_unique_slug(instance, value):
    """Make a slug and ensure it's unique for the model by adding -1, -2... if needed."""
    base_slug = slugify(value)[:200] 
    slug = base_slug
    Model = instance.__class__
    num = 1
    while Model.objects.filter(slug=slug).exclude(pk=getattr(instance, "pk", None)).exists():
        slug = f"{base_slug}-{num}"
        num += 1
    return slug


class Brand(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)

    class Meta:
        ordering = ['name']
        indexes = [Index(fields=['slug']), Index(fields=['name'])]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)

    class Meta:
        ordering = ['name']
        indexes = [Index(fields=['slug']), Index(fields=['name'])]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    rating = models.DecimalField(
        max_digits=3, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.0')), MaxValueValidator(Decimal('5.0'))],        default=0
    )
    in_stock = models.BooleanField(default=True, db_index=True)
    image_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            Index(fields=['price']),
            Index(fields=['rating']),
            Index(fields=['in_stock']),
            Index(fields=['created_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.brand.name})"


class CartItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.CASCADE, related_name='cart_items'
    )
    session_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at']
    
        constraints = [
            UniqueConstraint(fields=['user', 'product'], condition=Q(user__isnull=False), name='unique_user_product'),
            UniqueConstraint(fields=['session_id', 'product'], condition=Q(session_id__isnull=False), name='unique_session_product'),
        ]
        indexes = [Index(fields=['session_id']), Index(fields=['user'])]

    def __str__(self):
        who = self.user.username if self.user_id else f"session:{self.session_id}"
        return f"{who} - {self.product.name} x{self.quantity}"
