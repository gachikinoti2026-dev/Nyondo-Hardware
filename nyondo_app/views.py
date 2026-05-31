from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
import re
from .models import Product, Stock, Sales, SchemeCustomer, SchemePayment, SchemeGoodsPickup


# ===================== PRODUCTS =====================

def product_list(request):
    return render(request, "product_list.html", {
        "products": Product.objects.all().order_by("product_name")
    })


def product_create(request):
    if request.method == "POST":
        try:
            Product.objects.create(
                category_name=request.POST.get("category_name"),
                product_name=request.POST.get("product_name"),
                unit_cost=Decimal(request.POST.get("unit_cost")),
                unit_price=Decimal(request.POST.get("unit_price")),
                description=request.POST.get("description"),
            )
            messages.success(request, "Product created.")
            return redirect("product_list")
        except Exception as e:
            messages.error(request, str(e))

    return render(request, "product_form.html")


def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        try:
            product.category_name = request.POST.get("category_name")
            product.product_name = request.POST.get("product_name")
            product.unit_cost = Decimal(request.POST.get("unit_cost"))
            product.unit_price = Decimal(request.POST.get("unit_price"))
            product.description = request.POST.get("description")
            product.save()

            messages.success(request, "Product updated.")
            return redirect("product_list")
        except Exception as e:
            messages.error(request, str(e))

    return render(request, "edit_product.html", {"product": product})


def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        if product.total_stock() > 0:
            messages.error(request, "Cannot delete product with stock.")
        else:
            product.delete()
            messages.success(request, "Product deleted.")
        return redirect("product_list")

    return render(request, "delete_product.html", {"product": product})


# ===================== STOCK =====================

def stock_list(request):
    return render(request, "stock_list.html", {
        "stocks": Stock.objects.select_related("product"),
        "products": Product.objects.all()
    })





def add_stock(request):
    products = Product.objects.all()

    if request.method == "POST":
        try:
            product_id = request.POST.get("product")
            supplier_name = request.POST.get("supplier_name", "").strip()
            quantity = int(request.POST.get("quantity_received"))
            unit_cost = Decimal(request.POST.get("unit_cost"))
            unit_price = Decimal(request.POST.get("unit_price"))

            # Basic validation
            if not product_id or not supplier_name:
                raise Exception("Product and supplier name are required.")

            if quantity <= 0:
                raise Exception("Quantity must be greater than 0.")

            if unit_price <= unit_cost:
                raise Exception("Selling price must be greater than cost price.")

            Stock.objects.create(
                product_id=product_id,
                supplier_name=supplier_name,
                quantity_received=quantity,
                unit_cost=unit_cost,
                unit_price=unit_price,
                supplier_paid=request.POST.get("supplier_paid") == "on",
            )

            messages.success(request, "Stock added successfully.")
            return redirect("stock_list")

        except Exception as e:
            messages.error(request, str(e))

    #  Always render form (GET or error)
    return render(request, "stock_form.html", {
        "products": products
    })




def edit_stock(request, stock_id):
    stock = get_object_or_404(Stock, id=stock_id)

    if request.method == "POST":
        try:
            stock.product_id = request.POST.get("product")
            stock.supplier_name = request.POST.get("supplier_name")
            stock.quantity_received = int(request.POST.get("quantity_received"))
            stock.quantity_available = stock.quantity_received
            stock.unit_cost = Decimal(request.POST.get("unit_cost"))
            stock.unit_price = Decimal(request.POST.get("unit_price"))
            stock.supplier_paid = request.POST.get("supplier_paid") == "on"
            stock.save()

            messages.success(request, "Stock updated.")
            return redirect("stock_list")
        except Exception as e:
            messages.error(request, str(e))

    return render(request, "edit_stock.html", {
        "stock": stock,
        "products": Product.objects.all()
    })


def delete_stock(request, stock_id):
    stock = get_object_or_404(Stock, id=stock_id)

    if request.method == "POST":
        if stock.quantity_available < stock.quantity_received:
            messages.error(request, "Cannot delete sold stock.")
        else:
            stock.delete()
            messages.success(request, "Stock deleted.")
        return redirect("stock_list")

    return render(request, "delete_stock.html", {"stock": stock})





def stock_dashboard(request):
    stocks = Stock.objects.all()

    # Total stock records
    total_items = stocks.count()

    # Total quantity available
    total_quantity = stocks.aggregate(
        total=Sum("quantity_available")
    )["total"] or 0

    # Total available stock value (REAL value)
    total_value = sum(s.available_value() for s in stocks)

    #  ONLY unpaid supplier debt
    total_debt = stocks.filter(supplier_paid=False).aggregate(
        total=Sum("total_amount_due")
    )["total"] or 0

    # Optional: Paid stock value
    paid_value = stocks.filter(supplier_paid=True).aggregate(
        total=Sum("total_amount_due")
    )["total"] or 0

    # Low stock (threshold = 10)
    products = Product.objects.all()
    low_stock = [p for p in products if p.total_stock() <= 10]

    context = {
        "total_items": total_items,
        "total_quantity": total_quantity,
        "total_value": total_value,
        "total_debt": total_debt,
        "paid_value": paid_value,
        "low_stock": low_stock,
    }

    return render(request, "stock_dashboard.html", context)






def stock_report(request):
    stocks = Stock.objects.select_related("product")

    total_value = sum(s.available_value() for s in stocks)

    total_debt = stocks.filter(supplier_paid=False).aggregate(
        total=Sum("total_amount_due")
    )["total"] or 0

    return render(request, "stock_report.html", {
        "stocks": stocks,
        "total_value": total_value,
        "total_debt": total_debt,
    })



# ===================== SALES =====================

def sales_list(request):
    return render(request, "sales_list.html", {
        "sales": Sales.objects.select_related("product"),
        "products": Product.objects.all()
    })


def add_sale(request):
    products = Product.objects.all()
    selected_product = None

    if request.method == "POST":
        try:
            product_id = request.POST.get("product")
            selected_product = Product.objects.get(id=product_id)

            Sales.objects.create(
                customer_name=request.POST.get("customer_name"),
                customer_type=request.POST.get("customer_type"),
                product=selected_product,
                quantity=int(request.POST.get("quantity")),
                transport_required=request.POST.get("transport_required") == "on",
                distance_km=Decimal(request.POST.get("distance_km") or "0"),
            )

            messages.success(request, "Sale recorded.")
            return redirect("sales_list")

        except Exception as e:
            messages.error(request, str(e))

    return render(request, "salesform.html", {
        "products": products,
        "selected_product": selected_product
    })


def edit_sale(request, sale_id):
    sale = get_object_or_404(Sales, id=sale_id)

    if request.method == "POST":
        try:
            sale.customer_name = request.POST.get("customer_name")
            sale.customer_type = request.POST.get("customer_type")
            sale.product_id = request.POST.get("product")
            sale.quantity = int(request.POST.get("quantity"))
            sale.transport_required = request.POST.get("transport_required") == "on"
            sale.distance_km = Decimal(request.POST.get("distance_km") or "0")
            sale.save()

            messages.success(request, "Sale updated.")
            return redirect("sales_list")
        except Exception as e:
            messages.error(request, str(e))

    return render(request, "edit_sale.html", {
        "sale": sale,
        "products": Product.objects.all()
    })


def delete_sale(request, sale_id):
    sale = get_object_or_404(Sales, id=sale_id)

    if request.method == "POST":
        sale.delete()
        messages.success(request, "Sale deleted.")
        return redirect("sales_list")

    return render(request, "delete_sale.html", {"sale": sale})


def sales_dashboard(request):
    sales = Sales.objects.select_related("product")

    total_sales = sales.count()

    total_revenue = sales.aggregate(
        total=Sum("total_price")
    )["total"] or 0

    total_transport = sales.aggregate(
        total=Sum("transport_fee")
    )["total"] or 0

    # Average sale value
    avg_sale = total_revenue / total_sales if total_sales else 0

    # Recent sales
    recent_sales = sales.order_by("-sale_date")[:5]

    context = {
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "total_transport": total_transport,
        "avg_sale": avg_sale,
        "recent_sales": recent_sales,
    }

    return render(request, "sales_dashboard.html", context)

def sales_report(request):
    sales = Sales.objects.select_related("product")

    return render(request, "sales_report.html", {
        "sales": sales,
        "total_revenue": sales.aggregate(total=Sum("total_price"))["total"] or 0
    })


def sales_invoice(request, sale_id):
    sale = get_object_or_404(Sales, id=sale_id)

    return render(request, "sales_invoice.html", {
        "sale": sale,
        "goods_total": sale.total_price - sale.transport_fee
    })


# ===================== SCHEME =====================

def scheme_list(request):
    return render(request, "scheme_list.html", {
        "customers": SchemeCustomer.objects.all(),
        "payments": SchemePayment.objects.select_related("customer"),
        "pickups": SchemeGoodsPickup.objects.select_related("customer", "product"),
        "products": Product.objects.all()
    })




def add_scheme_customer(request):
    if request.method == "POST":
        try:
            full_name = request.POST.get("full_name", "").strip()
            nin = request.POST.get("nin_number", "").strip()
            phone = request.POST.get("phone_number", "").strip()

            # Validation
            if not full_name or not nin or not phone:
                raise Exception("All required fields must be filled.")

            phone_pattern = r"^(?:\+256|0)(7[0-9]{8})$"
            if not re.match(phone_pattern, phone):
                raise Exception("Enter a valid Ugandan phone number.")

            nin_pattern = r"^[A-Z]{2}[0-9A-Z]{10,12}$"
            if not re.match(nin_pattern, nin):
                raise Exception("Enter a valid NIN.")

            SchemeCustomer.objects.create(
                full_name=full_name,
                nin_number=nin,
                phone_number=phone,
                address=request.POST.get("address"),
                occupation=request.POST.get("occupation"),
                employer_name=request.POST.get("employer_name"),
            )

            messages.success(request, "Customer added.")
            return redirect("scheme_list")

        except Exception as e:
            messages.error(request, str(e))

    #  Render form (GET or error)
    return render(request, "scheme_customer_form.html")




def delete_scheme_customer(request, customer_id):
    customer = get_object_or_404(SchemeCustomer, id=customer_id)

    if request.method == "POST":
        customer.delete()
        messages.success(request, "Customer deleted.")
        return redirect("scheme_list")

    return render(request, "delete_scheme_customer.html", {"customer": customer})


def add_scheme_payment(request):
    customers = SchemeCustomer.objects.all()

    if request.method == "POST":
        try:
            customer_id = request.POST.get("customer")
            amount = Decimal(request.POST.get("amount_paid"))

            if not customer_id or amount <= 0:
                raise Exception("Valid customer and amount are required.")

            payment=SchemePayment.objects.create(
                customer_id=customer_id,
                amount_paid=amount,
                notes=request.POST.get("notes"),
            )

            messages.success(request, "Payment recorded.")
            return redirect("scheme_payment_receipt",payment_id = payment.id)

        except Exception as e:
            messages.error(request, str(e))

    return render(request, "scheme_payment_form.html", {
        "customers": customers
    })





def add_scheme_pickup(request):
    customers = SchemeCustomer.objects.all()
    products = Product.objects.all()

    if request.method == "POST":
        try:
            customer = get_object_or_404(
                SchemeCustomer, id=request.POST.get("customer")
            )
            product = get_object_or_404(
                Product, id=request.POST.get("product")
            )
            quantity = int(request.POST.get("quantity_taken"))

            # Validate quantity
            if quantity <= 0:
                raise Exception("Quantity must be greater than zero.")

            if quantity > product.total_stock():
                raise Exception("Not enough stock.")

            # Check customer balance
            total_cost = product.unit_price * quantity
            if total_cost > customer.available_balance():
                raise Exception("Insufficient balance.")

            # CREATE SALE
            sale = Sales.objects.create(
                customer_name=customer.full_name,
                customer_type="retail",
                product=product,
                quantity=quantity,
                transport_required=False,
            )

            # REDUCE STOCK (IMPORTANT)
            remaining = quantity
            stock_batches = Stock.objects.filter(
                product=product,
                quantity_available__gt=0
            ).order_by("date_received")

            for stock in stock_batches:
                if remaining <= 0:
                    break

                if stock.quantity_available >= remaining:
                    stock.quantity_available -= remaining
                    stock.save()
                    remaining = 0
                else:
                    remaining -= stock.quantity_available
                    stock.quantity_available = 0
                    stock.save()

            # Safety check
            if remaining > 0:
                raise Exception("Stock deduction error.")

            # RECORD PICKUP
            SchemeGoodsPickup.objects.create(
                customer=customer,
                product=product,
                quantity_taken=quantity,
                linked_sale=sale,
            )

            messages.success(request, "Pickup recorded successfully.")
            return redirect("scheme_list")

        except Exception as e:
            messages.error(request, str(e))

    # Render form
    return render(request, "scheme_pickup.html", {
        "customers": customers,
        "products": products
    })



def scheme_payment_receipt(request, payment_id):
    payment = get_object_or_404(
        SchemePayment.objects.select_related("customer"),
        id=payment_id
    )

    return render(request, "scheme_payment_receipt.html", {
        "payment": payment,
        "customer": payment.customer,
        "balance": payment.customer.available_balance(),
    })


def delete_scheme_payment(request, payment_id):
    payment = get_object_or_404(SchemePayment, id=payment_id)

    if request.method == "POST":
        payment.delete()
        messages.success(request, "Payment deleted successfully.")
        return redirect("scheme_list")

    return render(request, "delete_scheme_payment.html", {
        "payment": payment
    })



