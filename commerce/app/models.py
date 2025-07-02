from django.db import models
from django.contrib.auth.models import User

class Categories(models.Model):
    name = models.CharField(max_length=50,null=False)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name
    
class Product(models.Model):
    category = models.ForeignKey(Categories,on_delete=models.CASCADE)
    title = models.CharField(max_length=100,null=False)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10,decimal_places=2)
    discount_price = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)
    image = models.ImageField(upload_to='images/')
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return self.title
    
class UserProfile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    street = models.TextField(null=True, blank=True)
    city = models.TextField(null=True, blank=True)
    state = models.TextField(null=True, blank=True)
    pincode = models.PositiveIntegerField(null=True, blank=True)
    phone = models.CharField(max_length=10,blank=True)
    image = models.ImageField(upload_to='images/',null=True, blank=True)
    dob = models.DateField(null=True,blank=True)
    

    def __str__(self):
        return self.user.username

class Cart(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart,on_delete=models.CASCADE)
    products = models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)

    def get_total(self):
        if self.products.discount_price:
            return self.products.discount_price * self.quantity
        return self.products.price * self.quantity
    
ORDER_STATUS = (
    ('Pending','Pending'),
    ('Confirmed','Confirmed'),
    ('Shipped','Shipped'),
    ('Delivered','Delivered'),
    ('Cancelled','Cancelled'),
)

class Order(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart,on_delete=models.SET_NULL,null=True,blank=True)
    total_amount = models.DecimalField(max_digits=10,decimal_places=2)
    address = models.TextField()
    ordered_at = models.DateTimeField(auto_now_add=True)
    payment = models.CharField(max_length=100,blank=True)
    status = models.CharField(max_length = 200, choices=ORDER_STATUS,default='Pending')
    refund_status = models.CharField(
        max_length=50,
        default="Pending",
        choices=[
            ("Pending", "Pending"),
            ("Refunded", "Refunded"),
        ]
    )


    def __str__(self):
        return f"Order {self.id} by {self.user.username}"
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order,on_delete = models.CASCADE)
    product = models.ForeignKey(Product, on_delete = models.CASCADE)
    quantity = models.IntegerField(default=0)

class Review(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)    
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i,i) for i in range (1,6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.rating} by {self.user.username}"

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('user','product')