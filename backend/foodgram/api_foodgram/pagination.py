from rest_framework.pagination import PageNumberPagination


class UserPagination(PageNumberPagination):
    page_size = 6


class FoodgramPagePagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'
