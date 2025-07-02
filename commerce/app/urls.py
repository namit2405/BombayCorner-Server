from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token
urlpatterns = [
   path('', views.home, name="home"), 
   path('signup/',views.SignupView.as_view(),name='signup'),
   path('login/',views.LoginView.as_view(),name='login'),
   path('logout/',views.LogoutView.as_view(),name='logout'),
   path('api-token-auth/', obtain_auth_token),
   path('categories/',views.get_all_categories,name='get_all_categories'),
   path('products/',views.get_all_products,name='get_all_products'),
   path('products/categories/<int:category_id>/',views.get_products_by_category,name='get_products_by_categories'),
   path('products/top-rated/', views.get_top_rated_products, name='get_top_rated_products'),
   path('products/<int:pk>/', views.ProductDetailAPIView.as_view(), name='product-detail'),
   path('cart/',views.GetOrCreateCartView.as_view(),name="user-cart"),
   path('cart/add/',views.AddOrUpdateCartItem.as_view(),name="cart-add"),
   path('cart/update/<int:item_id>/',views.UpdateCartItemView.as_view(),name='cart-update'),
   path('cart/remove/<int:item_id>/',views.RemoveCartItemView.as_view(),name='cart-remove'),
   path('cart/detail/',views.CartDetailView.as_view(),name='cart-detail'),
   path('checkout/',views.CheckoutAPIView.as_view(),name="checkout"),
   path('order/status/<int:order_id>/',views.OrderStatus.as_view(),name="order-status"),
   path('order/history/',views.OrderHistory.as_view(),name='order-history'),
   path('order/<int:order_id>/cancel/', views.CancelOrderAPIView.as_view(), name='cancel-order'),
   path('wishlist/',views.WishlistlistAPIView.as_view(),name='wishlist'),
   path('wishlist/<int:pk>/',views.WishlistItemAPIView.as_view(),name='wishlist-delete'),
   path('reviews/',views.ReviewAPIView.as_view(),name='reviews'),
   path('products/search-suggestions/', views.search_suggestions,name='search_suggestions'),
   path('user/profile/', views.UserProfileDetail.as_view(), name='user-profile'),
   path('send-otp/', views.SendOTPView.as_view()),
   path('verify-otp/', views.VerifyOTPView.as_view()),
]

