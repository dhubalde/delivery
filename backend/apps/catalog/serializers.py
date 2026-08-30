from rest_framework import serializers

from apps.catalog.models import Category, Flavor, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "is_active", "position"]
        read_only_fields = ["id"]


class ProductSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField()
    min_flavors = serializers.IntegerField(required=False, allow_null=True)
    max_flavors = serializers.IntegerField(required=False, allow_null=True)
    pote_size = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    image = serializers.ImageField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "category_id",
            "name",
            "description",
            "price",
            "product_type",
            "pote_size",
            "min_flavors",
            "max_flavors",
            "image_url",
            "image",
            "is_active",
        ]
        read_only_fields = ["id"]

    def to_internal_value(self, data):
        mutable = data.copy() if hasattr(data, "copy") else dict(data)
        for k in ("min_flavors", "max_flavors", "category_id"):
            if k in mutable and mutable[k] == "":
                mutable[k] = None
        if "pote_size" in mutable and mutable["pote_size"] == "":
            mutable["pote_size"] = None
        if "image_url" in mutable and mutable["image_url"] == "":
            mutable["image_url"] = None
        return super().to_internal_value(mutable)

    def validate(self, attrs):
        ptype = attrs.get("product_type", getattr(self.instance, "product_type", None))
        pote_size = attrs.get("pote_size", getattr(self.instance, "pote_size", None))
        min_f = attrs.get("min_flavors", getattr(self.instance, "min_flavors", None))
        max_f = attrs.get("max_flavors", getattr(self.instance, "max_flavors", None))
        if self.instance is not None:
            for k in ("product_type", "pote_size", "min_flavors", "max_flavors"):
                if k not in attrs and k in self.initial_data:
                    pass
        has_flavors = not (min_f is None and max_f is None)
        if has_flavors:
            if min_f is None or max_f is None:
                raise serializers.ValidationError({"min_flavors": "Both min_flavors and max_flavors must be set or both null."})
            if not isinstance(min_f, int) or not isinstance(max_f, int):
                raise serializers.ValidationError({"min_flavors": "min_flavors/max_flavors must be integers."})
            if min_f < 1 or max_f > 4 or min_f > max_f:
                raise serializers.ValidationError({"min_flavors": "Require 1 <= min_flavors <= max_flavors <= 4."})
        if ptype == Product.ProductType.POTE:
            if not pote_size:
                if has_flavors:
                    raise serializers.ValidationError({"pote_size": "Pote products require pote_size when flavors are enabled."})
            else:
                if pote_size not in (Product.PoteSize.KG_1, Product.PoteSize.KG_HALF, Product.PoteSize.KG_QUARTER):
                    raise serializers.ValidationError({"pote_size": f"Invalid pote_size {pote_size}."})
        elif ptype == Product.ProductType.UNIT:
            if pote_size is not None:
                raise serializers.ValidationError({"pote_size": "Unit products must not define pote_size."})
        if "category_id" in attrs:
            from apps.catalog.models import Category as CatModel

            qs = CatModel.objects.filter(pk=attrs["category_id"])
            if not qs.exists() and not CatModel.all_objects.filter(pk=attrs["category_id"]).exists():
                raise serializers.ValidationError({"category_id": "Category does not exist."})
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if getattr(instance, "image", None) and getattr(instance.image, "name", None):
            request = self.context.get("request")
            try:
                url = instance.image.url
                if request is not None:
                    url = request.build_absolute_uri(url)
                data["image_url"] = url
            except Exception:
                pass
        return data


class FlavorSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Flavor
        fields = ["id", "category_id", "name", "is_active"]
        read_only_fields = ["id"]
