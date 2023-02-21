from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user


class CanSeeOriginalImage(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(allow_original_image=True)


class CanGenerateExpiringLinks(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(allow_expiring_link=True)

# class IsBasic(permissions.BasePermission):
#     """
#     Check if user plan is base
#     """
#
#     def has_permission(self, request, view):
#         return request.user.groups.filter(name="Basic")
#
#
# class IsPremium(permissions.BasePermission):
#     """
#     Check if user plan is premium
#     """
#
#     def has_permission(self, request, view):
#         return request.user.groups.filter(name="Premium")
#
#
# class IsEnterprise(permissions.BasePermission):
#     """
#     Check if user plan is enterprise
#     """
#
#     def has_permission(self, request, view):
#         return request.user.groups.filter(name="Enterprise")
