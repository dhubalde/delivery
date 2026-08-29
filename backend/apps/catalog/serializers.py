from rest_framework import serializers

from apps.catalog.models import Category, Flavor, Product, ProductFlavor


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "position", "is_active"]


class ProductSerializer(serializers.ModelSerializer):
    flavor_ids = serializers.ListField(child=serializers.IntegerField(), required=False, allow_empty=True, write_only=True)
    flavors = serializers.SerializerMethodField(read_only=True)
    merchant_id = serializers.IntegerField(required=False)
    category_id = serializers.IntegerField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "product_type",
            "pote_size",
            "min_flavors",
            "max_flavors",
            "is_active",
            "category_id",
            "merchant_id",
            "flavor_ids",
            "flavors",
        ]

    def get_flavors(self, obj):
        rel = getattr(obj, "suggested_flavors", None)
        if rel is not None:
            try:
                qs = rel.select_related("flavor").all()
                return [{"id": r.flavor_id, "name": r.flavor.name} for r in qs]
            except Exception:
                pass
        return []

    def validate(self, data):
        pt = data.get("product_type") or getattr(self.instance, "product_type", None)
        ps = data.get("pote_size") or getattr(self.instance, "pote_size", None)
        mn = data.get("min_flavors") if "min_flavors" in data else getattr(self.instance, "min_flavors", None)
        mx = data.get("max_flavors") if "max_flavors" in data else getattr(self.instance, "max_flavors", None)
        if pt == Product.ProductType.POTE:
            if ps is None or mn is None or mx is None:
                raise serializers.ValidationError({"pote_size": "Pote requires size and min/max flavors."})
            if mn < 1 or mx < 1 or mn > mx or mx > 4:
                raise serializers.ValidationError({"max_flavors": f"BR-CAT-04/05: allowed min 1-4 max 1-4, got min {mn} max {mx}"})
            if ps in (Product.PoteSize.KG_1, Product.PoteSize.KG_HALF):
                low, high = 1, 4
            elif ps == Product.PoteSize.KG_QUARTER:
                low, high = 1, 3
            else:
                low, high = 1, 4
            if mn < low or mx > high:
                raise serializers.ValidationError({"max_flavors": f"BR-CAT-04/05: for {ps} allowed {low}-{high}, got min {mn} max {mx}"})
        if pt == Product.ProductType.UNIT:
            if ps is not None or mn is not None or mx is not None:
                raise serializers.ValidationError({"product_type": "Unit must not have size/bounds"})
        flavor_ids = data.get("flavor_ids", None)
        if flavor_ids:
            uniq = list(dict.fromkeys(flavor_ids))
            if len(uniq) != len(flavor_ids):
                raise serializers.ValidationError({"flavor_ids": "Duplicated flavor ids."})
            qs = Flavor.objects.filter(id__in=flavor_ids)
            if qs.count() != len(set(flavor_ids)):
                raise serializers.ValidationError({"flavor_ids": "Algunos gustos no existen."})
            merchant = data.get("merchant") or getattr(self.instance, "merchant", None) if self.instance else data.get("merchant")
            merchant_id = None
            if merchant is not None:
                merchant_id = getattr(merchant, "id", None) or getattr(merchant, "pk", None) or merchant
            else:
                merchant_id = data.get("merchant_id")
                if merchant_id is None and self.instance:
                    merchant_id = getattr(self.instance, "merchant_id", None)
            if merchant_id is not None:
                if qs.exclude(merchant_id=merchant_id).exists():
                    raise serializers.ValidationError({"flavor_ids": "Todos los gustos deben pertenecer al mismo merchant."})
        return data

    def create(self, validated_data):
        flavor_ids = validated_data.pop("flavor_ids", [])
        if flavor_ids is None:
            flavor_ids = []
        if flavor_ids:
            qs = Flavor.objects.filter(id__in=flavor_ids)
            if qs.count() != len(set(flavor_ids)):
                raise serializers.ValidationError({"flavor_ids": "Algunos gustos no existen."})
            merchant = validated_data.get("merchant")
            merchant_id = getattr(merchant, "id", None) if merchant else validated_data.get("merchant_id")
            if merchant_id and qs.exclude(merchant_id=merchant_id).exists():
                raise serializers.ValidationError({"flavor_ids": "Todos los gustos deben pertenecer al mismo merchant."})
        product = super().create(validated_data)
        if not flavor_ids:
            return product
        for fid in flavor_ids:
            try:
                ProductFlavor.objects.create(product=product, flavor_id=fid)
            except Exception:
                pass
        return product

    def update(self, instance, validated_data):
        flavor_ids = validated_data.pop("flavor_ids", None)
        product = super().update(instance, validated_data)
        if flavor_ids is None:
            return product
        if not flavor_ids:
            product.suggested_flavors.all().delete()
            return product
        qs = Flavor.objects.filter(id__in=flavor_ids)
        if qs.count() != len(set(flavor_ids)):
            raise serializers.ValidationError({"flavor_ids": "Algunos gustos no existen."})
        if qs.exclude(merchant_id=product.merchant_id).exists():
            raise serializers.ValidationError({"flavor_ids": "Todos los gustos deben pertenecer al mismo merchant."})
        product.suggested_flavors.all().delete()
        for fid in flavor_ids:
            try:
                ProductFlavor.objects.create(product=product, flavor_id=fid)
            except Exception:
                pass
        return product


class FlavorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flavor
        fields = ["id", "name", "is_active", "category_id", "merchant_id"]
