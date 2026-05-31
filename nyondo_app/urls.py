from django.urls import path
from . import views

urlpatterns = [

    # ===================== PRODUCTS =====================
    path("products/", views.product_list, name="product_list"),
    path("products/create/", views.product_create, name="product_create"),
    path("products/edit/<int:product_id>/", views.edit_product, name="edit_product"),
    path("products/delete/<int:product_id>/", views.delete_product, name="delete_product"),


    # ===================== STOCK =====================
    path("stock/", views.stock_list, name="stock_list"),
    path("stock/add/", views.add_stock, name="add_stock"),
    path("stock/edit/<int:stock_id>/", views.edit_stock, name="edit_stock"),
    path("stock/delete/<int:stock_id>/", views.delete_stock, name="delete_stock"),
    path("stock/dashboard/", views.stock_dashboard, name="stock_dashboard"),
    path("stock/report/", views.stock_report, name="stock_report"),


    # ===================== SALES =====================
    path("sales/", views.sales_list, name="sales_list"),
    path("sales/add/", views.add_sale, name="add_sale"),
    path("sales/edit/<int:sale_id>/", views.edit_sale, name="edit_sale"),
    path("sales/delete/<int:sale_id>/", views.delete_sale, name="delete_sale"),
    path("sales/report/", views.sales_report, name="sales_report"),
    path("sales/dashboard/", views.sales_dashboard, name="sales_dashboard"),
    path("sales/invoice/<int:sale_id>/", views.sales_invoice, name="sales_invoice"),


    # ===================== SCHEME =====================
    path("scheme/", views.scheme_list, name="scheme_list"),
    path("scheme/customer/add/", views.add_scheme_customer, name="add_scheme_customer"),
    path("scheme/customer/delete/<int:customer_id>/", views.delete_scheme_customer, name="delete_scheme_customer"),
    path("scheme/payment/add/", views.add_scheme_payment, name="add_scheme_payment"),
    path("scheme/pickup/add/", views.add_scheme_pickup, name="add_scheme_pickup"),
    path( "scheme/payment/receipt/<int:payment_id>/",views.scheme_payment_receipt, name="scheme_payment_receipt"),
    path("scheme/payment/delete/<int:payment_id>/",views.delete_scheme_payment,name="delete_scheme_payment"),



]

