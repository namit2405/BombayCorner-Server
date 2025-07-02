from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from rest_framework.authtoken.models import Token
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import render
from .serializers import SignupSerializer
from .models import Categories,Product,Cart,CartItem,Order,OrderItem,Wishlist,Review, UserProfile
from .serializers import CategorySerializer,ProductSerializer,CartItemSerializer,CartSerializer,OrderSerializer,WishlistSerializer,ReviewSerializer, UserProfileSerializer
from rest_framework.decorators import api_view
from django.core.mail import send_mail
from django.db.models import Avg
from rest_framework.pagination import PageNumberPagination
from django.db.models import Avg, Q
from django.http import JsonResponse
from rapidfuzz import process, fuzz
from django.conf import settings
from rest_framework.generics import RetrieveAPIView
import random
from django.core.cache import cache

class SendOTPView(APIView):
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=400)

        otp = str(random.randint(100000, 999999))
        cache.set(f"otp_{email}", otp, timeout=300)  # OTP valid for 5 minutes

        # Send email
        send_mail(
            subject="Your OTP for Signup",
            message=f"Your OTP is {otp}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )
        return Response({"message": "OTP sent successfully"})

class VerifyOTPView(APIView):
    def post(self, request):
        email = request.data.get("email")
        entered_otp = request.data.get("otp")
        real_otp = cache.get(f"otp_{email}")

        if real_otp == entered_otp:
            return Response({"verified": True})
        return Response({"verified": False}, status=400)

def home(request):
    return render(request, "home.html")

class SignupView(APIView):
    def post(self, request, *args, **kwargs):
        print(request.data)
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            Token.objects.create(user=user)
            return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
        else:
            print(serializer.errors)  # Debug line
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self,request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key,'username':user.username}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    
class LogoutView(APIView):
    authenticate_class = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def  post(self, request):
        request.user.auth_token.delete()
        return Response({'message':'Logged out successfully'},status=status.HTTP_200_OK)
    
@api_view(['GET'])
def get_all_categories(request):
    categories = Categories.objects.all()
    serializer = CategorySerializer(categories,many=True,context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def get_all_products(request):
    products = Product.objects.all().annotate(avg_rating=Avg('review__rating'))

    # Filters
    category_id = request.GET.get('category_id')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    min_rating = request.GET.get('min_rating')

    if category_id:
        products = products.filter(category_id=category_id)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    if min_rating:
        products = products.filter(avg_rating__gte=min_rating)

    # Search (exact & fuzzy)
    search_query = request.GET.get('search', '').strip()
    if search_query:
        search_query_lower = search_query.lower()
        threshold = 60  # Adjust as needed for fuzzy match tolerance (0–100)

        matching_products = []
        for product in products:
            title_lower = product.title.lower() if product.title else ''
            desc_lower = product.description.lower() if product.description else ''
            cat_lower = product.category.name.lower() if product.category else ''

            # Calculate similarity scores
            score_title = fuzz.partial_ratio(search_query_lower, title_lower)
            score_desc = fuzz.partial_ratio(search_query_lower, desc_lower)
            score_cat = fuzz.partial_ratio(search_query_lower, cat_lower)

            # Keep product if any field exceeds threshold
            if max(score_title, score_desc, score_cat) > threshold:
                matching_products.append(product)

        # Use only the matching products
        products = matching_products

    # Pagination
    paginator = PageNumberPagination()
    paginator.page_size = 12
    result_page = paginator.paginate_queryset(products, request)

    serializer = ProductSerializer(result_page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)




@api_view(['GET'])
def get_products_by_category(request,category_id):
    try:
        category = Categories.objects.get(id=category_id)
    except Categories.DoesNotExist:
        return Response({"error":"Category Not Found"},status=404)
    
    products = Product.objects.filter(category=category)
    serializer = ProductSerializer(products,many=True,context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def get_top_rated_products(request):
    products = Product.objects.annotate(avg_rating=Avg('review__rating')).order_by('-avg_rating')[:5]
    serializer = ProductSerializer(products, many=True, context={'request': request})
    return Response(serializer.data)

class ProductDetailAPIView(RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class GetOrCreateCartView(APIView): 
    permission_classes = [IsAuthenticated]
    
    def  get(self,request):
        cart,created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)   
        return Response(serializer.data)

class AddOrUpdateCartItem(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))
        
        cart, _ = Cart.objects.get_or_create(user=request.user)
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)
        
        cart_item, created = CartItem.objects.get_or_create(cart=cart, products=product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()
        
        # Serialize the updated/created cart_item
        serializer = CartItemSerializer(cart_item)
        
        return Response({
            "message": "Product added to cart",
            "cart_item": serializer.data  # <-- this is the key for your frontend
        }, status=201)

    
class UpdateCartItemView(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self,request,item_id):
        try:
            cart_item = CartItem.objects.get(id=item_id,cart__user=request.user)
        except CartItem.DoesNotExist:
            return Response({"error":"Cart Item Not Found"}, status = 404)

        new_quantity = request.data.get("quantity")
        if new_quantity is not None:
            cart_item.quantity = int(new_quantity)
            cart_item.save()
            return Response({"message":"Quantity updated Successfully"})
        else:
            return Response({"Error":"Quantity Not Provided"},status=404)
class RemoveCartItemView(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self,request,item_id):
        try:
            cart_item = CartItem.objects.get(id=item_id,cart__user=request.user)
            cart_item.delete()
            return Response({"message":"Item removed from cart"})
        except CartItem.DoesNotExist:
            return Response({"error":"Item not found"},status=404)
        
class CartDetailView(APIView):
    def get(self,request):
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        total = sum(item.quantity * item.products.price for item in cart_items)
        serializer = CartItemSerializer(cart_items, many=True)
        return Response({
            "cart_items": serializer.data,
            "total": total
        })

class CheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self,request):
        try:
            cart = Cart.objects.get(user = request.user)
        except Cart.DoesNotExist:
            return Response({
                "error" : "Cart is empty"
            },status = status.HTTP_404_BAD_REQUEST)

        cart_items = CartItem.objects.filter(cart = cart)
        if not cart_items.exists():
            return Response({
                "error" : "Cart is empty"
            },status = status.HTTP_400_BAD_REQUEST)

        total = 0
        for item in cart_items:
            total += item.products.price * item.quantity
        
        address = request.data.get("address")
        if not address:
            return Response({"error":"Address is required"},status = status.HTTP_400_BAD_REQUEST)
        
        order = Order.objects.create(
            user = request.user,
            cart = cart,
            total_amount = total,
            address = address,
            payment = "Confirmed",
            status = 'Confirmed',
        )
        
        for item in cart_items:
            OrderItem.objects.create(
                order = order,
                product = item.products,
                quantity = item.quantity
            )
        
        cart_items.delete()
        subject = f"Order Confirmation - Order #{order.id}"
        message = (
            f"Dear {request.user.first_name},\n\n"
            f"Thank you for shopping with us!\n\n"
            f"Here are your order details:\n"
            f"Order ID: {order.id}\n"
            f"Order Date: {order.ordered_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Total Amount: ₹{order.total_amount}\n"
            f"Shipping Address: {order.address}\n\n"
            f"We will notify you once your order is shipped.\n\n"
            f"If you have any questions, feel free to contact us at {settings.DEFAULT_FROM_EMAIL}.\n\n"
            f"Thank you for choosing us!\n\n"
            f"Best Regards,\n"
            f"The {settings.SITE_NAME} Team"
        )

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,         # Sender
            [order.user.email],                  # Recipient
            fail_silently=False,
        )
        
        send_mail(
    subject=f"🔔 New Order Received - Order #{order.id}",
    message=(
        f"A new order has been placed on your store.\n\n"
        f"Customer: {request.user.username} ({request.user.email})\n"
        f"Order ID: {order.id}\n"
        f"Total: ₹{order.total_amount}\n"
        f"Address: {order.address}\n\n"
        f"Please check your admin dashboard for details."
    ),
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=["jainnamit34@gmail.com"],  # ✅ correct
    fail_silently=False,
)

        
        

        
        serializer = OrderSerializer(order)
        return Response({"message":"Order Placed Successfully","order":serializer.data},status=status.HTTP_201_CREATED)
    
class OrderStatus(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order doesn't exist"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

        
        
class OrderHistory(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        orders = Order.objects.filter(user = request.user).order_by('-ordered_at')
        serializer = OrderSerializer(orders,many=True)
        print(serializer.data)
        return Response(serializer.data)
    
class CancelOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if order.status in ['Pending', 'Confirmed']:
            order.status = 'Cancelled'
            order.save()
            send_mail(
    'Order Cancelled',
    f'Your order #{order.id} has been cancelled.',
    'no-reply@yourshop.com',  # from_email
    [order.user.email],
    fail_silently=True,
            )
            return Response({"message": "Order cancelled successfully", "status": order.status}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Order cannot be cancelled at this stage"}, status=status.HTTP_400_BAD_REQUEST)

    
class WishlistlistAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        wishlist =  Wishlist.objects.filter(user = request.user)
        serializer = WishlistSerializer(wishlist,many=True) 
        return Response(serializer.data,status=status.HTTP_200_OK)
    def post(self,request):
        serializer = WishlistSerializer(data=request.data,context={'request':request})
        if serializer.is_valid():
            serializer.save(user = request.user)
            return Response(serializer.data,status=status.HTTP_201_CREATED) 
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WishlistItemAPIView(APIView):
    permission_classes = [IsAuthenticated] 
    def delete(self,request,pk):
        try:
            wishlist_item = Wishlist.objects.filter(pk=pk, user = request.user)
        except Wishlist.DoesNotExist:
            return Response({"error":"Item Not Found"},status=status.HTTP_404_NOT_FOUND)
        wishlist_item.delete()
        return Response({'message':'Item Delete Successfully'},status=status.HTTP_204_NO_CONTENT)

class ReviewAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        product_id = request.query_params.get('product')
        if product_id:
            reviews = Review.objects.filter(product_id = product_id)
        else:
            reviews = Review.objects.all()
        serializer = ReviewSerializer(reviews,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    def post(self,request):
        serializer = ReviewSerializer(data=request.data, context={'request':request})
        if serializer.is_valid():
            serializer.save(user = request.user)
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST) 

@api_view(['GET'])
def search_suggestions(request):
    q = request.GET.get("q", "").strip()
    suggestions = []

    if q:
        # Product title suggestions (icontains)
        product_qs = Product.objects.filter(title__icontains=q)[:10]
        for product in product_qs:
            suggestions.append({"type": "product", "value": product.title})

        # Category suggestions (icontains)
        category_qs = Categories.objects.filter(name__icontains=q)[:5]
        for cat in category_qs:
            suggestions.append({"type": "category", "value": cat.name})

        # Fuzzy match for similar product titles
        all_titles = list(Product.objects.values_list('title', flat=True))
        fuzzy_titles = process.extract(
            q, all_titles, scorer=fuzz.partial_ratio, limit=5
        )
        for title, score, _ in fuzzy_titles:
            if score > 60 and not any(s["value"] == title for s in suggestions):
                suggestions.append({"type": "similar", "value": title})

        # Fuzzy match for similar category names
        all_cats = list(Categories.objects.values_list('name', flat=True))
        fuzzy_cats = process.extract(
            q, all_cats, scorer=fuzz.partial_ratio, limit=3
        )
        for name, score, _ in fuzzy_cats:
            if score > 60 and not any(s["value"] == name for s in suggestions):
                suggestions.append({"type": "similar_category", "value": name})

    return JsonResponse(suggestions, safe=False)


class UserProfileDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request):
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)