from django import template

register = template.Library()

@register.filter
def activeClass(value,arg):
	return value.replace(arg,'active')
