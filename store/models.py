from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('fashion', 'Fashion'),
        ('electronics', 'Electronics'),
        ('mobiles', 'Mobiles'),
        ('appliances', 'Appliances'),
        ('other', 'Other'),
    ]

    SUBCATEGORY_CHOICES = [
        # Fashion
        ('fashion_men', 'Men'),
        ('fashion_women', 'Women'),
        # Electronics
        ('electronics_headsets', 'Headsets'),
        ('electronics_laptops', 'Laptops'),
        ('electronics_accessories', 'Accessories'),
        # Mobiles
        ('mobiles_iphone', 'iPhone'),
        ('mobiles_samsung', 'Samsung'),
        ('mobiles_oppo', 'OPPO'),
        ('mobiles_nothing', 'Nothing'),
        ('mobiles_motorola', 'Motorola'),
        # Other
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='fashion')
    subcategory = models.CharField(max_length=30, choices=SUBCATEGORY_CHOICES, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    image_url = models.URLField(max_length=500, blank=True, help_text="Paste an image link here")

    def __str__(self):
        return self.name

    def average_rating(self):
        """Calculate average rating from reviews"""
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(review.rating for review in reviews) / reviews.count(), 1)
        return 0.0

    def review_count(self):
        """Get total number of reviews"""
        return self.reviews.count()

class ProductImage(models.Model):
    """Store multiple images for each product"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField(max_length=500, help_text="Paste an image link here")
    is_primary = models.BooleanField(default=False, help_text="Use this as the main image on product list")
    display_order = models.PositiveIntegerField(default=0, help_text="Order of display (0 = first)")
    
    class Meta:
        ordering = ['display_order']
    
    def __str__(self):
        return f"{self.product.name} - Image {self.display_order + 1}"

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE) 
    quantity = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

# ==========================================
# NEW ORDER MODELS FOR CHECKOUT
# ==========================================

class Order(models.Model):
    # Status choices for delivery tracking
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default='Pending'
    )

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2) # Freezes the price at the time of purchase
    quantity = models.PositiveIntegerField(default=1)

    def subtotal(self):
        # Guard against legacy/bad rows where price may be null.
        if self.price is None:
            return Decimal('0.00')
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order #{self.order.id})"

# ==========================================
# USER ADDRESS MODEL - INDIA SPECIFIC
# ==========================================

class UserAddress(models.Model):
    """User address with Indian-specific fields"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='address')
    
    # Full Name
    full_name = models.CharField(max_length=100)
    
    # Phone number
    phone = models.CharField(max_length=20)
    
    # Address fields
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    
    # PIN Code (Indian postal code)
    pin_code = models.CharField(max_length=6, help_text="6-digit PIN code")
    
    # Country (default India)
    country = models.CharField(max_length=50, default='India')
    
    # Landmark (optional, common in India)
    landmark = models.CharField(max_length=200, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.city}, {self.state}"

# ==========================================
# WISHLIST MODEL
# ==========================================

class Wishlist(models.Model):
    """User wishlist for saving favorite products"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')
    created_at = models.DateTimeField(auto_now_add=True)
    
class WishlistItem(models.Model):
    """Individual item in a user's wishlist"""
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('wishlist', 'product')  # Prevent duplicate products in wishlist
    
class ProductReview(models.Model):
    """User reviews and ratings for products"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    review_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'product')  # One review per user per product
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}'s review of {self.product.name} - {self.rating} stars"