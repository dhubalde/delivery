from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    recipient_type_label = serializers.CharField(source="get_recipient_type_display", read_only=True)
    type_label = serializers.CharField(source="get_type_display", read_only=True)
    order_code = serializers.IntegerField(source="order.code", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "merchant",
            "recipient_type",
            "recipient_type_label",
            "recipient_name",
            "order",
            "order_code",
            "message",
            "type",
            "type_label",
            "is_read",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "merchant",
            "recipient_type",
            "recipient_name",
            "order",
            "message",
            "type",
            "is_read",
            "created_at",
        ]