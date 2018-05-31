import xadmin

# Register your models here.

from . import models
from xadmin import views


class BaseSetting(object):
    enable_themes = True
    use_bootswatch = True


xadmin.site.register(views.BaseAdminView,BaseSetting)


class GlobalSettings(object):
    site_title = "美多商城运营管理系统"
    site_footer = "美多商城集团有限公司"
    menu_style = "accordion"


xadmin.site.register(views.CommAdminView,GlobalSettings)


class SKUAdmin(object):
    model_icon = 'fa fa-gift'
    list_display = ['id', 'name', 'price', 'stock', 'sales', 'comments']
    search_fields = ['id','name']
    list_filter = ['category']
    ordering = ['id']
    readonly_fields = ['sales', 'comments']
    list_editable = ['price', 'stock']
    show_detail_fields = ['name']
    show_bookmarks = True
    list_export = ['xls', 'csv', 'xml']

    def save_models(self):
        obj = self.new_obj
        obj.save()
        from celery_tasks.html.tasks import generate_static_sku_detail_html
        generate_static_sku_detail_html.delay(obj.id)


class SKUSpecificationAdmin(object):
    def save_models(self):
        obj = self.new_obj
        obj.save()
        from celery_tasks.html.tasks import generate_static_sku_detail_html
        generate_static_sku_detail_html.delay(obj.sku.id)

    def delete_model(self):
        obj = self.obj
        sku_id = obj.sku.id
        obj.delete()
        from celery_tasks.html.tasks import generate_static_sku_detail_html
        generate_static_sku_detail_html.delay(sku_id)


class SKUImageAdmin(object):
    def save_models(self):
        obj = self.new_obj
        obj.save()
        from celery_tasks.html.tasks import generate_static_sku_detail_html
        generate_static_sku_detail_html.delay(obj.sku.id)

        # 设置SKU默认图片
        sku = obj.sku
        if not sku.default_image_url:
            sku.default_image_url = obj.image.url
            sku.save()

    def delete_model(self):
        obj = self.obj
        sku_id = obj.sku.id
        obj.delete()
        from celery_tasks.html.tasks import generate_static_sku_detail_html
        generate_static_sku_detail_html.delay(sku_id)


class GoodsCategoryAdmin(object):
    list_per_page = 20

    def save_models(self):
        obj = self.new_obj
        obj.save()
        from celery_tasks.html.tasks import generate_static_list_search_html
        generate_static_list_search_html.delay()

    def delete_model(self):
        obj = self.obj
        obj.delete()
        from celery_tasks.html.tasks import generate_static_list_search_html
        generate_static_list_search_html.delay()


class GoodsChannelAdmin(object):
    def save_models(self):
        obj = self.new_obj
        obj.save()
        from celery_tasks.html.tasks import generate_static_list_search_html
        generate_static_list_search_html.delay()

    def delete_model(self):
        obj = self.obj
        obj.delete()
        from celery_tasks.html.tasks import generate_static_list_search_html
        generate_static_list_search_html.delay()


xadmin.site.register(models.GoodsCategory, GoodsCategoryAdmin)
xadmin.site.register(models.GoodsChannel, GoodsChannelAdmin)
xadmin.site.register(models.Goods)
xadmin.site.register(models.Brand)
xadmin.site.register(models.GoodsSpecification)
xadmin.site.register(models.SpecificationOption)
xadmin.site.register(models.SKU, SKUAdmin)
xadmin.site.register(models.SKUSpecification, SKUSpecificationAdmin)
xadmin.site.register(models.SKUImage, SKUImageAdmin)
