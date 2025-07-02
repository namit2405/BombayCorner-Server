from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Categories, Product, UserProfile, Cart, CartItem, Order, OrderItem, Review, Wishlist

# User Serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'street', 'city', 'state', 'pincode', 'phone', 'image', 'dob']

# Signup Serializer (if needed separately)
class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

# Category Serializer
class CategorySerializer(serializers.ModelSerializer):
    first_product_image_url = serializers.SerializerMethodField()
    class Meta:
        model = Categories
        fields = ['id', 'name', 'slug', 'first_product_image_url']
    
    def get_first_product_image_url(self, obj):
        # Get the first product of this category
        first_product = Product.objects.filter(category=obj).first()
        if first_product and first_product.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(first_product.image.url)
            else:
                return first_product.image.url  # or return None
        return None

# Product Serializer
class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Categories.objects.all(), source='category', write_only=True
    )

    # Add this field!
    avg_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'description', 'price', 'discount_price',
            'image', 'quantity', 'category', 'category_id', 'avg_rating'
        ]


# CartItem Serializer
class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(source='products', read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='products', write_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'product', 'product_id', 'quantity', 'total']

    def get_total(self, obj):
        return obj.get_total()

# Cart Serializer
class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(source='cartitem_set', many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'created_at', 'items']

# OrderItem Serializer
class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product', write_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'product', 'product_id', 'quantity']

# Order Serializer
class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    items = OrderItemSerializer(source='orderitem_set', many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'cart', 'total_amount', 'address', 'ordered_at', 'payment', 'items', 'status','refund_status']

# Review Serializer
class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product', write_only=True)

    class Meta:
        model = Review
        fields = ['id', 'product', 'user', 'rating', 'product_id', 'comment', 'created_at',]
        read_only_fields = ['user', 'created_at']

# Wishlist Serializer
class WishlistSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product', write_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'product', 'product_id']
