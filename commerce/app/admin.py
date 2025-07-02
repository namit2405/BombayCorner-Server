from django.contrib import admin
from . import models

admin.site.register(models.Categories)
admin.site.register(models.Product)
admin.site.register(models.UserProfile)
admin.site.register(models.Cart)
admin.site.register(models.CartItem)
@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "refund_status", "ordered_at")
    list_filter = ("status", "refund_status")

    readonly_fields = ("ordered_at",)  # ✅ mark ordered_at as read-only

    def get_readonly_fields(self, request, obj=None):
        """
        Make refund_status read-only unless status is Cancelled
        Also keep ordered_at always read-only
        """
        fields = list(super().get_readonly_fields(request, obj)) + ['ordered_at']
        if obj and obj.status != 'Cancelled':
            fields.append('refund_status')
        return fields

    def get_fields(self, request, obj=None):
        """
        Dynamically control field visibility
        """
        fields = ['user', 'cart', 'total_amount', 'address', 'payment', 'status', 'ordered_at']
        if obj and obj.status == 'Cancelled':
            fields.append('refund_status')
        return fields
admin.site.register(models.OrderItem)
admin.site.register(models.Review)
admin.site.register(models.Wishlist)
