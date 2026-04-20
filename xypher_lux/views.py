from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import UserRegistrationForm, SetPasswordForm, AddToCartForm, UpdateCartItemForm, CheckoutForm
from django.contrib.auth.decorators import login_required
from .models import Category, Product, UserProfile, PasswordResetCode, Cart, CartItem, Product, Order, OrderItem,  Notification, WishlistItem, ShippingAddress
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
import random
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import F
from decimal import Decimal
from django.views.decorators.http import require_POST
import uuid
import logging

logger = logging.getLogger(__name__)
# Create your views here.

@require_http_methods(["POST", "GET"])

def signup_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                # Create user
                user = User.objects.create_user(
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    username=form.cleaned_data['email'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'],
                )
                
                # Create associated profile
                full_phone = f"{form.cleaned_data['country_code']}{form.cleaned_data['phone_number']}"
                UserProfile.objects.create(
                    user=user,
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    email=form.cleaned_data["email"],
                    phone_number=full_phone,
                )
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Registration successful. You can now log in.'
                }, status=200)
                
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error during registration: {str(e)}'
                }, status=500)  # Use 500 for server errors
        else:
            # Form validation failed
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list[0] if error_list else 'Invalid value'
            
            return JsonResponse({
                'status': 'error',
                'message': 'Please correct the errors below.',
                'errors': errors
            }, status=400)
    
    return render(request, 'xypher_lux/product/list.html')

def login_view(request):
    # If user is already authenticated, redirect to home
    if request.user.is_authenticated:
        # ✅ Return JSON so apiFetch can handle it consistently
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'message': 'Already logged in.',
                'redirect_url': reverse('xypher_lux:dashboard')
            })
        return redirect('xypher_lux:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next')
            redirect_url = next_url if next_url else reverse('xypher_lux:dashboard')
            return JsonResponse({'message': 'Login successful.', 'redirect_url': redirect_url})
        else:
            return JsonResponse({'message': 'Invalid username or password.'}, status=400)
            # GET request — render the login page
    return redirect('xypher_lux:product_list')  # ✅ double-check this template path

def forgot_password_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)

            last_code = PasswordResetCode.objects.filter(user=user).order_by("-created_at").first()
            if last_code and (timezone.now() - last_code.created_at) < timedelta(minutes=2):
                # Error: Return JSON error response
                return JsonResponse({'message': "Please wait at least two minutes before requesting a new code."}, status=400)

            PasswordResetCode.objects.filter(user=user).delete()

            code = str(random.randint(10000, 99999))
            PasswordResetCode.objects.create(user=user, code=code)

            send_mail(
                "Password Reset Code",
                f"Your password reset code is {code}.\nPlease do not share it with anyone.",
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            # Success: Return JSON success response
            return JsonResponse({'message': "Check your email for the reset code."})

        except User.DoesNotExist:
            # Error: Return JSON error response
            return JsonResponse({'message': "Email address does not exist."}, status=400)

    # For GET requests, render the page
    return render(request, "xypher_lux/product/list.html")

def verify_code_view(request):
    if request.method == "POST":
        code = request.POST.get("code")
        try:
            password_reset_code = PasswordResetCode.objects.get(user=user, code=code)
            
            if (timezone.now() - password_reset_code.created_at) > timedelta(minutes=10):
                password_reset_code.delete()
                # Error: Return JSON error response
                return JsonResponse({'message': "Password reset code expired. Request a new one."}, status=400)
            
            request.session["reset_user_id"] = password_reset_code.user.id
            password_reset_code.delete()
            
            # Success: Return JSON success response with redirect URL
            return JsonResponse({'message': "Code verified successfully.", 'redirect_url': 'xypher_lux:set_new_password'})

        except PasswordResetCode.DoesNotExist:
            # Error: Return JSON error response
            return JsonResponse({'message': "Invalid code, please try again."}, status=400)

    # For GET requests, render the page
    return render(request, "xypher_lux/product/list.html")

def set_new_password_view(request):
    user_id = request.session.get("reset_user_id")
    if not user_id:
        # Error: Return JSON error response
        return JsonResponse({'message': "Your password reset session has expired, please try again."}, status=400)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        # Error: Return JSON error response
        return JsonResponse({'message': "Unexpected error occurred, please try again."}, status=400)
    
    if request.method == 'POST':
        form = SetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            user.set_password(new_password)
            user.save()
            del request.session['reset_user_id']
            # Success: Return JSON success response with redirect URL
            return JsonResponse({'message': 'Your password has been reset successfully. You can now log in.'})
        else:
            # Form validation failed: Return JSON error response
            errors = {field: errors[0] for field, errors in form.errors.items()}
            return JsonResponse({'message': 'Please correct the errors.', 'errors': errors}, status=400)
    
    # For GET requests, render the page
    return render(request, 'xypher_lux/product/list.html')

@login_required(login_url="xypher_lux:login")
def dashboard_view(request, category_slug=None):
    user = request.user

    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True)
    cart = Cart.objects.filter(user=user, is_active=True).first()
    
    featured_products = Product.objects.filter(
        is_featured=True,
        is_active=True
    )[:4]

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    all_products = list(
        Product.objects.filter(
            is_active=True
        ).values_list('id', flat=True)
    )
    random_ids = random.sample(all_products, min(4, len(all_products)))
    recommended_products = Product.objects.filter(id__in=random_ids)

    return render(request, "xypher_lux/dashboard.html", {
        "user": user,
        "category": category,
        "categories": categories,
        "products": products,
        "featured_products": featured_products,
        "recommended_products": recommended_products,
    })


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('xypher_lux:product_list')

@login_required(login_url="xypher_lux:login")
def profile_view(request):

    user = request.user
    profile = user.userprofile # assumes a OneToOne User profile model

    context = {
        'profile': profile,
        'orders': Order.objects.filter(user=user).order_by('created_at'),
        'notifications': Notification.objects.filter(user=user).order_by('-created_at')[:5],  # latest 5 notifications
        'wishlist': WishlistItem.objects.filter(user=user).order_by('-added_at')[:10],  # latest 10 wishlist items
        "unread_notifications_count": Notification.objects.filter(user=user, is_read=False).count(),
        "shipping_addresses": ShippingAddress.objects.filter(user=user).order_by('-created_at')[:5],  # latest 5 addresses
    }
    return render(request, 'xypher_lux/profile.html', context)

@login_required(login_url="xypher_lux:login")
def update_profile_view(request):
    if request.method != 'POST':
        return JsonResponse({"message": "Invalid request method."}, status=405)

    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)  # ✅ safe

    user.first_name = request.POST.get("first_name", user.first_name)
    user.last_name  = request.POST.get("last_name", user.last_name)
    user.email      = request.POST.get("email", user.email)
    user.save()

    profile.phone       = request.POST.get("phone", profile.phone)
    profile.address     = request.POST.get("address", profile.address)
    profile.city        = request.POST.get("city", profile.city)
    profile.postal_code = request.POST.get("postal_code", profile.postal_code)
    profile.save()

    return JsonResponse({"message": "Profile updated successfully."})
@login_required(login_url="xypher_lux:login")
def update_password_view(request):
    if request.method != POST:
        return JsonResponse({"message": "invalid request method"}, status=405)
    
    form = SetPassword(request.POST)

    if not form.is_valid():
        # return the first validation error message from the form
        error = form.error_as_data()
        frst_error = next(iter(errors.value()))[0].message
        return JsonRespomse({"messsage": first_error}, status=400)

    user = request.user
    user.set_password(form.cleaned_data['new_password'])
    user.save()

    update_session_auth_hash(request, user)

    return JsonResponse({"message": "pssword updated successfully"})

@login_required(login_url="xypher_lux:login")
def delete_account_view(request):
    if request.method != 'POST':
        return JsonResponse({"message": "Invalid request method."}, status=400)
    
    user = request.user
    user.delete()

    return JsonResponse({"message": "Account deleted asuccessfully", 
    "redirect_url": reverse("xypher_lux:product_list")
    })

def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True)

    featured_products = Product.objects.filter(
        is_featured=True,
        is_active=True
    )[:4]
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # Randomly recommend products 
    all_products = list(
        Product.objects.filter(
            is_active=True
        ).values_list('id', flat=True)
    )
    random_ids = random.sample(all_products, min(4, len(all_products)))
    recommended_products = Product.objects.filter(id__in=random_ids)
    
    return render(request, 'xypher_lux/product/list.html', {
        'category': category,
        'categories': categories,
        'products': products,
        "featured_products": featured_products,
        "recommended_products": recommended_products,
    })

def mens_collection_view(request):
    mens_categories = Category.objects.filter(name__iexact="men")
    products = Product.objects.filter(
        category__in=mens_categories,
        is_active=True
    ).select_related('category').order_by('-created_at')

    featured = Product.objects.filter(
        category__in=mens_categories,
        is_active=True,
        is_featured=True
    )[:4] # show maximum 4 featured products

    selected_category = request.GET.get('category')
    if selected_category:
        products = products.filter(category__slug=selected_category)

    return render(request, 'xypher_lux/men.html', {
        'products': products,
        'mens_categories': mens_categories,
        'selected_category': selected_category,
        'total': products.count(),
        'featured': featured,
    })

def women_collection_view(request):
    women_categories = Category.objects.filter(name__iexact="women")
    products = Product.objects.filter(
        category__in=women_categories,
        is_active=True
    ).select_related("category").order_by("created_at")

    featured_products = Product.objects.filter(
        is_featured=True,
        is_active=True
    )[:4]

    selected_category = request.GET.get("category")
    if selected_category:
        products = products.filter(category__slug=selected_category)

    return render(request, "xypher_lux/women.html", {
        "products": products,
        "women_categories": women_categories,
        "selected_category": selected_category,
        "total": products.count(),
    })
    

def search_view(request):
    query = request.GET.get('q', '')
    products = Product.objects.none()

    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query),
            is_active= True
        ).select_related('category').distinct()

    return render(request, 'xypher_lux/search.html', {
        'query': query,
        'products': products,
        'total': products.count(),
    })

def product_detail_view(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, is_active=True)

    # similar products - same category, exclude current

    similar_products = Product.objects.filter(
        category = product.category,
        is_active = True
    ).exclude(id=product.id)[:6]

    featured_products = Product.objects.filter(
        is_featured=True,
        is_active=True
    ).exclude(id=product.id)[:4]

    return render(request, "xypher_lux/detail.html", {
    "product" : product,
    "similar_products": similar_products,
    "featured_products": featured_products, 
    })

@login_required
def cart_view(request):
    """Display the shopping cart"""
    cart = get_or_create_cart(request.user)
    cart_items = cart.items.select_related('product').all()
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': cart.subtotal,
        'shipping_cost': cart.shipping_cost,
        'total': cart.total,
        'total_items': cart.total_items,
    }
    
    return render(request, 'xypher_lux/product/list.html', context)


@login_required
@require_POST
def add_to_cart_view(request):
    """Add item to cart via AJAX"""
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))
    size = request.POST.get('size', '')
    color = request.POST.get('color', '')
    
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Check stock availability
        if quantity > product.stock:
            return JsonResponse({
                'success': False,
                'message': f'Only {product.stock} items available in stock'
            }, status=400)
        
        cart = get_or_create_cart(request.user)
        pyth
        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            size=size,
            color=color,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Update quantity if item already exists
            new_quantity = cart_item.quantity + quantity
            if new_quantity > product.stock:
                return JsonResponse({
                    'success': False,
                    'message': f'Cannot add more. Only {product.stock} items available'
                }, status=400)
            cart_item.quantity = new_quantity
            cart_item.save()
        
        return JsonResponse({
            'success': True,
            'message': f'{product.name} added to cart',
            'cart_total_items': cart.total_items,
            'cart_total': str(cart.total)
        })
        
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Product not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@require_POST
def update_cart_item_view(request, item_id):
    """Update cart item quantity"""
    try:
        cart = get_or_create_cart(request.user)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity < 1:
            return JsonResponse({
                'success': False,
                'message': 'Quantity must be at least 1'
            }, status=400)
        
        if quantity > cart_item.product.stock:
            return JsonResponse({
                'success': False,
                'message': f'Only {cart_item.product.stock} items available'
            }, status=400)
        
        cart_item.quantity = quantity
        cart_item.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Cart updated successfully',
            'item_total': str(cart_item.total_price),
            'cart_subtotal': str(cart.subtotal),
            'cart_total': str(cart.total),
            'cart_total_items': cart.total_items
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@require_POST
def remove_from_cart_view(request, item_id):
    """Remove item from cart"""
    try:
        cart = get_or_create_cart(request.user)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
        product_name = cart_item.product.name
        cart_item.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'{product_name} removed from cart',
            'cart_subtotal': str(cart.subtotal),
            'cart_total': str(cart.total),
            'cart_total_items': cart.total_items
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
def clear_cart_view(request):
    """Clear all items from cart"""
    cart = get_or_create_cart(request.user)
    cart.items.all().delete()
    
    messages.success(request, 'Cart cleared successfully')
    return redirect('cart_view')


@login_required
def checkout_view(request):
    """Checkout process"""
    cart = get_or_create_cart(request.user)
    
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty')
        return redirect('cart_view')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Create order
            order = form.save(commit=False)
            order.user = request.user
            order.order_number = f'ORD-{uuid.uuid4().hex[:8].upper()}'
            order.subtotal = cart.subtotal
            order.shipping_cost = cart.shipping_cost
            order.total = cart.total
            order.save()
            
            # Create order items from cart items
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    product_name=cart_item.product.name,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price,
                    size=cart_item.size,
                    color=cart_item.color
                )
                
                # Update product stock
                cart_item.product.stock = F('stock') - cart_item.quantity
                cart_item.product.save()
            
            # Clear cart
            cart.items.all().delete()
            cart.is_active = False
            cart.save()
            
            messages.success(request, f'Order {order.order_number} placed successfully!')
            return redirect('order_confirmation', order_id=order.id)
    else:
        form = CheckoutForm()
    
    context = {
        'form': form,
        'cart': cart,
        'cart_items': cart.items.select_related('product').all(),
    }
    
    return render(request, 'xypher_lux/product/list.html', context)


@login_required
def order_confirmation_view(request, order_id):
    """Order confirmation page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.select_related('product').all()
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    
    return render(request, 'xypher_lux/product/list.html', context)


@login_required
def order_history_view(request):
    """Display user's order history"""
    orders = Order.objects.filter(user=request.user).prefetch_related('items')
    
    context = {
        'orders': orders,
    }
    
    return render(request, 'xypher_lux/product/list.html', context)


@login_required
def order_detail_view(request, order_id):
    """Display order details"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.select_related('product').all()
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    
    return render(request, 'xypher_lux/product/list.html', context)