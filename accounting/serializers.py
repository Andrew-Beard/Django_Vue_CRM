from rest_framework import serializers
from .models import Item, Invoice, InvoiceItem, Client


class InvoiceClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ('uuid', 'name')


class ItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = Item
        fields = ['description']


class InvoiceItemSerializer(serializers.ModelSerializer):
    details = ItemSerializer(source='item')

    class Meta:
        model = InvoiceItem
        fields = ['price', 'amount', 'details']


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, label='items')
    client = serializers.CharField(source="client.name")

    class Meta:
        model = Invoice
        fields = ['uuid', 'reference', 'client', 'items']

    # def create(self, validated_data):
    #     item_items = validated_data.pop('items')
    #     invoice = Invoice.objects.create(**validated_data)
    #     for item_item in item_items:
    #         InvoiceItem.objects.create(invoice=invoice, **item_item)
    #     return invoice
