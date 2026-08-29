from rest_framework import serializers

from apps.catalog.models import Category, Flavor, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "is_active", "position"]
        read_only_fields = ["id"]


class ProductSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField()

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
            "is_active",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        ptype = attrs.get("product_type", getattr(self.instance, "product_type", None))
        pote_size = attrs.get("pote_size", getattr(self.instance, "pote_size", None))
        min_f = attrs.get("min_flavors", getattr(self.instance, "min_flavors", None))
        max_f = attrs.get("max_flavors", getattr(self.instance, "max_flavors", None))
        if self.instance is not None:
            for k in ("product_type", "pote_size", "min_flavors", "max_flavors"):
                if k not in attrs and k in self.initial_data:
                    pass
        if ptype == Product.ProductType.POTE:
            if not pote_size:
                raise serializers.ValidationError({"pote_size": "Pote products require pote_size."})
            if min_f is None or max_f is None:
                raise serializers.ValidationError({"min_flavors": "Pote products require min_flavors/max_flavors."})
            expected = {
                Product.PoteSize.KG_1: (3, 4),
                Product.PoteSize.KG_HALF: (3, 4),
                Product.PoteSize.KG_QUARTER: (2, 3),
            }
            bounds = expected.get(pote_size)
            if bounds is None:
                raise serializers.ValidationError({"pote_size": f"Invalid pote_size {pote_size}."})
            exp_min, exp_max = bounds
            if min_f != exp_min or max_f != exp_max:
                raise serializers.ValidationError(
                    {"min_flavors": f"{pote_size} requires min={exp_min} max={exp_max}, got min={min_f} max={max_f}."}
                )
            if min_f > max_f:
                raise serializers.ValidationError({"min_flavors": "min_flavors must be <= max_flavors."})
        elif ptype == Product.ProductType.UNIT:
            if pote_size is not None:
                raise serializers.ValidationError({"pote_size": "Unit products must not define pote_size."})
            if min_f is not None or max_f is not None:
                raise serializers.ValidationError({"product_type": "Unit products must not define flavor bounds."})
        if "category_id" in attrs:
            from apps.catalog.models import Category as CatModel

            qs = CatModel.objects.filter(pk=attrs["category_id"])
            if not qs.exists() and not CatModel.all_objects.filter(pk=attrs["category_id"]).exists():
                raise serializers.ValidationError({"category_id": "Category does not exist."})
        return attrs


class FlavorSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Flavor
        fields = ["id", "category_id", "name", "is_active"]
        read_only_fields = ["id"]
