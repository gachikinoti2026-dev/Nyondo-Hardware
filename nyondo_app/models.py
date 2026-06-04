from decimal import Decimal
from django.db import models
from django.db.models import Sum
from django.core.exceptions import ValidationError


# ===================== PRODUCT =====================

class Product(models.Model):
    CATEGORY_CHOICES = [
        ("cement", "Cement"),
        ("iron_bar", "Iron Bar"),
        ("iron_sheets", "Iron Sheets"),
        ("barbed_wires", "Barbed wires"),
        ("others", "Others"),
        ("nails", "Nails"),
        ("paint", "Paint"),
    ]

    category_name = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    product_name = models.CharField(max_length=100)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(blank=True)

    def clean(self):
        if self.unit_price <= self.unit_cost:
            raise ValidationError("Selling price must be greater than cost price.")

    def total_stock(self):
        return self.stock_set.aggregate(
            total=Sum("quantity_available")
        )["total"] or 0

    def __str__(self):
        return self.product_name


# ===================== STOCK =====================



class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    supplier_name = models.CharField(max_length=100)
    quantity_received = models.PositiveIntegerField()
    quantity_available = models.PositiveIntegerField(default=0)

    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    total_amount_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    supplier_paid = models.BooleanField(default=False)

    date_received = models.DateTimeField(auto_now_add=True)

    # Validation
    def clean(self):
        if self.unit_price <= self.unit_cost:
            raise ValidationError("Selling price must be greater than cost price.")

    # Save logic
    def save(self, *args, **kwargs):
        is_new = self.pk is None

        # Set available quantity on first save
        if is_new:
            self.quantity_available = self.quantity_received

        # Calculate supplier debt
        self.total_amount_due = self.quantity_received * self.unit_cost

        super().save(*args, **kwargs)

        # Sync product pricing AFTER saving
        Product.objects.filter(id=self.product_id).update(
            unit_cost=self.unit_cost,
            unit_price=self.unit_price
        )

    #  Total value of received stock
    def total_value(self):
        return self.quantity_received * self.unit_cost

    # REAL current stock value (important)
    def available_value(self):
        return self.quantity_available * self.unit_cost

 
    def __str__(self):
        return f"{self.product.product_name} - {self.quantity_available} available"




# ===================== SALES =====================

class Sales(models.Model):
    CUSTOMER_TYPES = [
        ("retail", "Retail"),
        ("wholesale", "Wholesale"),
        ("individual_buyers", "Individual Buyers"),
    ]

    customer_name = models.CharField(max_length=150)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPES)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transport_required = models.BooleanField(default=False)
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    transport_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sale_date = models.DateTimeField(auto_now_add=True)

    def clean(self):
        available_stock = self.product.total_stock()
        if self.quantity > available_stock:
            raise ValidationError("Not enough stock available.")

    def calculate_transport_fee(self, goods_total):
        if not self.transport_required:
            return Decimal("0.00")

        if self.distance_km <= Decimal("10") and goods_total >= Decimal("500000"):
            return Decimal("0.00")

        return Decimal("30000.00")

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        goods_total = self.product.unit_price * self.quantity
        self.transport_fee = self.calculate_transport_fee(goods_total)
        self.total_price = goods_total + self.transport_fee

        self.full_clean()
        super().save(*args, **kwargs)

        # Deduct stock using FIFO
        if is_new:
            remaining = self.quantity

            stocks = Stock.objects.filter(
                product=self.product,
                quantity_available__gt=0
            ).order_by("date_received")

            for stock in stocks:
                if remaining <= 0:
                    break

                used = min(stock.quantity_available, remaining)
                stock.quantity_available -= used
                stock.save(update_fields=["quantity_available"])
                remaining -= used

    def __str__(self):
        return f"{self.product.product_name} - {self.quantity} units"


# ===================== SCHEME =====================

class SchemeCustomer(models.Model):
    full_name = models.CharField(max_length=150)
    nin_number = models.CharField(max_length=30, unique=True)
    phone_number = models.CharField(max_length=20)
    address = models.TextField()
    occupation = models.CharField(max_length=100, default="Salary Earner")
    employer_name = models.CharField(max_length=150, blank=True)
    date_registered = models.DateTimeField(auto_now_add=True)

    def total_deposits(self):
        return self.schemepayment_set.aggregate(
            total=Sum("amount_paid")
        )["total"] or Decimal("0.00")

    def total_goods_taken(self):
        total = Decimal("0.00")
        for pickup in self.schemegoodspickup_set.select_related("linked_sale"):
            if pickup.linked_sale:
                total += pickup.linked_sale.total_price
        return total

    def available_balance(self):
        return self.total_deposits() - self.total_goods_taken()

    def __str__(self):
        return self.full_name


class SchemePayment(models.Model):
    customer = models.ForeignKey(SchemeCustomer, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.customer.full_name} - {self.amount_paid}"


class SchemeGoodsPickup(models.Model):
    customer = models.ForeignKey(SchemeCustomer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_taken = models.PositiveIntegerField()
    linked_sale = models.ForeignKey(
        Sales,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    pickup_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.full_name} - {self.product.product_name}"

