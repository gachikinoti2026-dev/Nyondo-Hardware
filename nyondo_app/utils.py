import datetime
import random
from .models import Sale

def generate_receipt_number():
    last_sale = Sale.objects.order_by('id').last()
    if last_sale and last_sale.receipt_number:
        try:
            last_num = int(last_sale.receipt_number.split('-')[-1])
            return f"RCPT-{last_num + 1}"
        except ValueError:
            return "RCPT-1000"
    return "RCPT-1000"
