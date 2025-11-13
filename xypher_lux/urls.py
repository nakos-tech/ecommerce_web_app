from django.urls import path
from . import views

app_name = "xypher_lux"

urlpatterns = [
    path('', views.product_list, name='product_list'),
          # Authentication URLs
    path('signup/', views.signup_view, name='signup_view'),
    path('login/', views.login_view, name='login_view'),
    path('forgot_password/', views.forgot_password_view, name='forgot_password'),
    path('verify_code/', views.verify_code_view, name='verify_code'),
    path('set_new_password/', views.set_new_password_view, name='set_new_password'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    # path('<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),

        # Cart URLs
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/', views.add_to_cart_view, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item_view, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart_view, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart_view, name='clear_cart'),
    
    # Checkout URLs
    path('checkout/', views.checkout_view, name='checkout'),
    path('order/confirmation/<int:order_id>/', views.order_confirmation_view, name='order_confirmation'),
    
    # Order History URLs
    path('orders/', views.order_history_view, name='order_history'),
    path('orders/<int:order_id>/', views.order_detail_view, name='order_detail'),
]

