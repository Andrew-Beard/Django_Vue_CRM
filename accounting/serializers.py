from rest_framework import serializers
from django.db import transaction
from .models import Item, Invoice, InvoiceItem, Client, ClientDetail, Currency
from django.shortcuts import get_object_or_404
import json


class ClientDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientDetail
        fields = ['address', 'zip', 'city', 'country', 'email', 'phone', 'vat', 'commerce']


class ClientSerializer(serializers.ModelSerializer):
    details = ClientDetailSerializer()

    class Meta:
        model = Client
        fields = ['uuid', 'name', 'details']

    @transaction.atomic
    def create(self, data):
        details_data = data.pop('details')
        client = self.Meta.model.objects.create(company=self.context['request'].user.employee.company, **data)
        # details_data['client'] = client
        print(details_data)

        detail_serializer = ClientDetailSerializer(client=client, **details_data)
        if detail_serializer.is_valid():  # PageSerializer does the validation
            detail_serializer.save()
        else:
            raise serializers.ValidationError(detail_serializer.errors)  # throws errors if any
        return client
        # client_data = data.pop('name')
        # details = ClientDetailSerializer.create(ClientDetailSerializer(), validated_data=client_data)
        # student, created = Client.objects.create(details=details, name=data.pop('name'))
        # return student


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['description', 'uuid']


class InvoiceItemSerializer(serializers.ModelSerializer):
    details = ItemSerializer(source='item')

    class Meta:
        model = InvoiceItem
        fields = ['price', 'amount', 'details']


class InvoiceSerializer(serializers.ModelSerializer):
    client = serializers.CharField(source="client.name")
    total = serializers.SerializerMethodField(method_name='get_total_price')

    class Meta:
        model = Invoice
        fields = ['uuid', 'reference', 'client', 'total']

    def get_total_price(self, instance):
        items = InvoiceItem.objects.filter(invoice=instance)
        total = 0

        for item_item in items:
            total += item_item.price
        return total


class InvoiceDetailSerializer(serializers.ModelSerializer):
    client = serializers.CharField(source="client.name")
    items = InvoiceItemSerializer(many=True, label='items')

    class Meta:
        model = Invoice
        fields = ['uuid', 'reference', 'client', 'items']

    @transaction.atomic
    def create(self, data):
        client_uuid = data['client']
        currency_pk = data['currency']
        reference = data['reference']
        # item_json = data['items']

        if not client_uuid or not currency_pk or not reference or not item_json:
            return {'status': 'ERROR', 'message': 'Fields missing'}

        client_item = get_object_or_404(Client, uuid=client_uuid)
        currency_item = get_object_or_404(Currency, pk=currency_pk)
        if not client_item.company == self.context['request'].user.employee.company:
            return {'status': 'ERROR', 'message': 'Client not found'}

        # todo add try catch
        Invoice.objects.create(
            client=client_item,
            reference=reference,
            currency=currency_item,
        )
        invoice = Invoice.objects.latest('id')
        item_items = json.loads(item_json)
        print(item_items)
        for key in item_items:
            # todo create item if not existing
            item_item = get_object_or_404(Item, uuid=key)
            if not item_item.company == self.context['request'].user.employee.company:
                return {'status': 'ERROR', 'message': 'Item not found'}

            InvoiceItem.objects.create(
                invoice=invoice,
                item=item_item,
                price=item_items[key]['price'],
                amount=item_items[key]['amount'],
            )
            print(item_items[key]['amount'])

        return {'status': 'SUCCESS', 'message': 'Invoice created'}
