from django.db import models
from customers.models import Customer
from products.models import Product


class Order(models.Model):
    ORDER_FINISHED = "Order_Finished"
    PREPARING = "Preparing"
    ORDER_READY = "Order_Ready"
    ORDER_DELIVERING = "Order_Delivering"
    ORDER_DELIVERED = "Order_Delivered"
    PAYMENT_CASH = "Cash"
    PAYMEMNT_SMART_WALLET = "Smart_Wallet"
    PAYMENT_VISA = "Visa"
    ORDER_STATUS = {
        ORDER_FINISHED: "Order Finished",
        PREPARING: "Preparing",
        ORDER_READY: "Order Ready",
        ORDER_DELIVERING: "Oreder Delivering",
        ORDER_DELIVERED: "Order Delivered"
    }
    ORDER_PAYMENT = {
        PAYMENT_CASH: "Cash",
        PAYMENT_VISA: "Visa",
        PAYMEMNT_SMART_WALLET: "Smart Wallet"
    }
    status = models.CharField(max_length=50, choices=ORDER_STATUS, default=ORDER_FINISHED)
    sub_total = models.FloatField()
    discount_total = models.FloatField(null=True, blank=True)
    tax_total = models.FloatField()
    shipping_price = models.FloatField()
    grand_price = models.FloatField()
    customer = models.ForeignKey(Customer, on_delete=models.SET_DEFAULT, default=0)
    address = models.CharField(max_length=300)
    payment_status = models.CharField(max_length=50, choices=ORDER_PAYMENT)
    
    def __str__(self):
        return f"order:{self.id} is {self.status} with payment: {self.payment_status} to {self.customer.first_name} {self.customer.last_name}"
    
    
class OrderItems(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_DEFAULT, default=0)
    quantity = models.PositiveIntegerField()
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.quantity} Items of {self.product.title} in {self.order.id}"
