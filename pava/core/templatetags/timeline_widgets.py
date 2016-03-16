from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.inclusion_tag('widgets/category.html', takes_context=True)
def category_widget(context, category):
    transactions = category[2]
    transactions.sort(key=lambda x: x['date'])
    return {
            'category_name': category[0],
            'transactions': transactions,
        }


@register.inclusion_tag('widgets/merchant.html', takes_context=True)
def merchant_widget(context, category):
    transactions = category[2]
    transactions.sort(key=lambda x: x['date'])
    return {
            'category_name': category[0],
            'transactions': transactions,
        }
