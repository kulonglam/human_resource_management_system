"""SCIM 2.0 Users + Groups provisioning for IdPs."""

from __future__ import annotations

import re

from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.audit import log_action
from api.permissions import HasAPIKeyScope, IsAdmin
from api.throttles import SCIMRateThrottle
from accounts.models import CustomUser, Role


SCIM_USER_SCHEMA = 'urn:ietf:params:scim:schemas:core:2.0:User'
SCIM_GROUP_SCHEMA = 'urn:ietf:params:scim:schemas:core:2.0:Group'
SCIM_LIST = 'urn:ietf:params:scim:api:messages:2.0:ListResponse'
SCIM_ERROR = 'urn:ietf:params:scim:api:messages:2.0:Error'
SCIM_PATCH = 'urn:ietf:params:scim:api:messages:2.0:PatchOp'


class ScimAuthMixin:
    permission_classes = [IsAdmin, HasAPIKeyScope]
    throttle_classes = [SCIMRateThrottle]
    required_api_scopes = ['scim', 'admin']


def _scim_error(detail, status_code=400, scim_type=None):
    body = {
        'schemas': [SCIM_ERROR],
        'detail': detail,
        'status': str(status_code),
    }
    if scim_type:
        body['scimType'] = scim_type
    return Response(body, status=status_code)


def _parse_eq_filter(filter_query, attr):
    """Parse simple `attr eq "value"` filters."""
    if not filter_query:
        return None
    pattern = rf'{attr}\s+eq\s+"([^"]+)"'
    match = re.search(pattern, filter_query, flags=re.IGNORECASE)
    return match.group(1) if match else None


def user_to_scim(user):
    groups = []
    if user.role_id:
        groups.append({
            'value': str(user.role_id),
            'display': user.role.name,
            '$ref': f'/api/v1/scim/v2/Groups/{user.role_id}',
        })
    return {
        'schemas': [SCIM_USER_SCHEMA],
        'id': str(user.id),
        'externalId': user.external_id or '',
        'userName': user.username,
        'name': {
            'givenName': user.first_name or '',
            'familyName': user.last_name or '',
            'formatted': user.get_full_name() or user.username,
        },
        'emails': [{'value': user.email, 'primary': True, 'type': 'work'}],
        'active': user.is_active,
        'groups': groups,
        'meta': {
            'resourceType': 'User',
            'location': f'/api/v1/scim/v2/Users/{user.id}',
        },
    }


def group_to_scim(role, *, include_members=True):
    members = []
    if include_members:
        for user in CustomUser.objects.filter(role=role, is_active=True).order_by('id')[:200]:
            members.append({
                'value': str(user.id),
                'display': user.username,
                '$ref': f'/api/v1/scim/v2/Users/{user.id}',
            })
    return {
        'schemas': [SCIM_GROUP_SCHEMA],
        'id': str(role.id),
        'displayName': role.name,
        'members': members,
        'meta': {
            'resourceType': 'Group',
            'location': f'/api/v1/scim/v2/Groups/{role.id}',
        },
    }


class ScimServiceProviderConfigView(ScimAuthMixin, APIView):
    def get(self, request):
        return Response({
            'schemas': ['urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig'],
            'patch': {'supported': True},
            'bulk': {'supported': False, 'maxOperations': 0, 'maxPayloadSize': 0},
            'filter': {'supported': True, 'maxResults': 200},
            'changePassword': {'supported': False},
            'sort': {'supported': False},
            'etag': {'supported': False},
            'authenticationSchemes': [{
                'type': 'oauthbearertoken',
                'name': 'API Key Bearer',
                'description': 'Use Authorization: Bearer <api-key> with scim scope.',
                'specUri': 'https://tools.ietf.org/html/rfc6750',
                'primary': True,
            }],
            'meta': {
                'resourceType': 'ServiceProviderConfig',
                'location': '/api/v1/scim/v2/ServiceProviderConfig',
            },
        })


class ScimResourceTypesView(ScimAuthMixin, APIView):
    def get(self, request):
        return Response({
            'schemas': [SCIM_LIST],
            'totalResults': 2,
            'Resources': [
                {
                    'schemas': ['urn:ietf:params:scim:schemas:core:2.0:ResourceType'],
                    'id': 'User',
                    'name': 'User',
                    'endpoint': '/Users',
                    'schema': SCIM_USER_SCHEMA,
                },
                {
                    'schemas': ['urn:ietf:params:scim:schemas:core:2.0:ResourceType'],
                    'id': 'Group',
                    'name': 'Group',
                    'endpoint': '/Groups',
                    'schema': SCIM_GROUP_SCHEMA,
                },
            ],
        })


class ScimSchemasView(ScimAuthMixin, APIView):
    def get(self, request):
        return Response({
            'schemas': [SCIM_LIST],
            'totalResults': 2,
            'Resources': [
                {'id': SCIM_USER_SCHEMA, 'name': 'User', 'description': 'User Account'},
                {'id': SCIM_GROUP_SCHEMA, 'name': 'Group', 'description': 'Role Group'},
            ],
        })


class ScimUsersView(ScimAuthMixin, APIView):
    """SCIM Users collection and create."""

    def get(self, request):
        start = int(request.query_params.get('startIndex', 1))
        count = min(int(request.query_params.get('count', 100)), 200)
        qs = CustomUser.objects.select_related('role', 'organization').order_by('id')
        filter_query = request.query_params.get('filter', '')
        username = _parse_eq_filter(filter_query, 'userName')
        external_id = _parse_eq_filter(filter_query, 'externalId')
        email = _parse_eq_filter(filter_query, 'emails.value') or _parse_eq_filter(filter_query, 'email')
        if username:
            qs = qs.filter(username=username)
        if external_id:
            qs = qs.filter(external_id=external_id)
        if email:
            qs = qs.filter(email__iexact=email)
        org_id = getattr(request.user, 'organization_id', None)
        if org_id:
            qs = qs.filter(organization_id=org_id)
        total = qs.count()
        users = qs[start - 1:start - 1 + count]
        return Response({
            'schemas': [SCIM_LIST],
            'totalResults': total,
            'startIndex': start,
            'itemsPerPage': len(users),
            'Resources': [user_to_scim(user) for user in users],
        })

    def post(self, request):
        email = (request.data.get('emails') or [{}])[0].get('value') or request.data.get('userName')
        username = request.data.get('userName') or (email or '').split('@')[0]
        if not username or not email:
            return _scim_error('userName and emails[0].value required', 400)
        if CustomUser.objects.filter(username=username).exists():
            return _scim_error('User already exists', 409, 'uniqueness')
        role_name = Role.EMPLOYEE
        for group in request.data.get('groups') or []:
            display = (group.get('display') or '').lower()
            if display in (Role.ADMIN, Role.MANAGER, Role.EMPLOYEE):
                role_name = display
        role, _ = Role.objects.get_or_create(name=role_name)
        org = request.user.organization if getattr(request.user, 'organization_id', None) else None
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=get_random_string(32),
            role=role,
            organization=org,
            external_id=request.data.get('externalId', '') or '',
            first_name=(request.data.get('name') or {}).get('givenName', ''),
            last_name=(request.data.get('name') or {}).get('familyName', ''),
            is_active=request.data.get('active', True),
        )
        log_action(request, 'create', 'CustomUser', user.id, username, 'SCIM provisioned')
        return Response(user_to_scim(user), status=status.HTTP_201_CREATED)


class ScimUserDetailView(ScimAuthMixin, APIView):
    def _get_user(self, pk):
        qs = CustomUser.objects.select_related('role', 'organization')
        org_id = None  # filled in get/patch
        return qs, org_id

    def get(self, request, pk):
        try:
            user = CustomUser.objects.select_related('role').get(pk=pk)
        except (CustomUser.DoesNotExist, ValueError):
            return _scim_error('User not found', 404)
        org_id = getattr(request.user, 'organization_id', None)
        if org_id and user.organization_id and user.organization_id != org_id:
            return _scim_error('User not found', 404)
        return Response(user_to_scim(user))

    def put(self, request, pk):
        return self._upsert(request, pk, partial=False)

    def patch(self, request, pk):
        return self._upsert(request, pk, partial=True)

    def delete(self, request, pk):
        try:
            user = CustomUser.objects.get(pk=pk)
        except (CustomUser.DoesNotExist, ValueError):
            return _scim_error('User not found', 404)
        user.is_active = False
        user.save(update_fields=['is_active'])
        log_action(request, 'update', 'CustomUser', user.id, user.username, 'SCIM deactivated')
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _upsert(self, request, pk, *, partial):
        try:
            user = CustomUser.objects.select_related('role').get(pk=pk)
        except (CustomUser.DoesNotExist, ValueError):
            return _scim_error('User not found', 404)

        data = request.data or {}
        if partial and data.get('schemas') and SCIM_PATCH in data.get('schemas', []):
            for op in data.get('Operations') or []:
                path = (op.get('path') or '').lower()
                value = op.get('value')
                op_name = (op.get('op') or 'replace').lower()
                if op_name not in ('replace', 'add'):
                    continue
                if path in ('active',) or (not path and isinstance(value, dict) and 'active' in value):
                    user.is_active = bool(value if path else value.get('active'))
                if path == 'externalid' or (isinstance(value, dict) and 'externalId' in value):
                    user.external_id = value if path else value.get('externalId', '')
                if path == 'name.givenname' or (isinstance(value, dict) and 'name' in value):
                    if path:
                        user.first_name = value or ''
                    else:
                        user.first_name = (value.get('name') or {}).get('givenName', user.first_name)
                if path == 'name.familyname':
                    user.last_name = value or ''
                if isinstance(value, dict) and 'name' in value and not path:
                    user.last_name = (value.get('name') or {}).get('familyName', user.last_name)
        else:
            if 'active' in data:
                user.is_active = bool(data.get('active'))
            if 'externalId' in data:
                user.external_id = data.get('externalId') or ''
            name = data.get('name') or {}
            if 'givenName' in name:
                user.first_name = name.get('givenName') or ''
            if 'familyName' in name:
                user.last_name = name.get('familyName') or ''
            emails = data.get('emails') or []
            if emails and emails[0].get('value'):
                user.email = emails[0]['value']
            if data.get('userName') and not partial:
                user.username = data['userName']
        user.save()
        log_action(request, 'update', 'CustomUser', user.id, user.username, 'SCIM updated')
        return Response(user_to_scim(user))


class ScimGroupsView(ScimAuthMixin, APIView):
    def get(self, request):
        start = int(request.query_params.get('startIndex', 1))
        count = min(int(request.query_params.get('count', 100)), 200)
        qs = Role.objects.all().order_by('id')
        display = _parse_eq_filter(request.query_params.get('filter', ''), 'displayName')
        if display:
            qs = qs.filter(name__iexact=display)
        total = qs.count()
        roles = list(qs[start - 1:start - 1 + count])
        return Response({
            'schemas': [SCIM_LIST],
            'totalResults': total,
            'startIndex': start,
            'itemsPerPage': len(roles),
            'Resources': [group_to_scim(role) for role in roles],
        })


class ScimGroupDetailView(ScimAuthMixin, APIView):
    def get(self, request, pk):
        try:
            role = Role.objects.get(pk=pk)
        except (Role.DoesNotExist, ValueError):
            return _scim_error('Group not found', 404)
        return Response(group_to_scim(role))

    def patch(self, request, pk):
        """Add/remove members (users) from a role group."""
        try:
            role = Role.objects.get(pk=pk)
        except (Role.DoesNotExist, ValueError):
            return _scim_error('Group not found', 404)
        for op in request.data.get('Operations') or []:
            op_name = (op.get('op') or '').lower()
            path = (op.get('path') or '').lower()
            value = op.get('value')
            members = value if isinstance(value, list) else ([value] if value else [])
            if 'member' not in path and op_name not in ('add', 'remove', 'replace'):
                continue
            for member in members:
                if not isinstance(member, dict):
                    continue
                user_id = member.get('value')
                try:
                    user = CustomUser.objects.get(pk=user_id)
                except (CustomUser.DoesNotExist, ValueError, TypeError):
                    continue
                if op_name in ('add', 'replace'):
                    user.role = role
                    user.save(update_fields=['role'])
                elif op_name == 'remove' and user.role_id == role.id:
                    emp_role, _ = Role.objects.get_or_create(name=Role.EMPLOYEE)
                    user.role = emp_role
                    user.save(update_fields=['role'])
        log_action(request, 'update', 'Role', role.id, role.name, 'SCIM group members updated')
        return Response(group_to_scim(role))
