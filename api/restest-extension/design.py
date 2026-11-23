"""Frozen sample and assertion menu for the RESTestBench FastAPI pilot."""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Scenario:
    name: str
    path: str
    method: str
    fixture: str
    checks: tuple[str, ...]


STATUS = {f'http_{code}': f'The response status is exactly HTTP {code}.'
          for code in (200, 400, 401, 403, 404, 422)}
DESCRIPTIONS = {
    **STATUS,
    'success': 'The response status is any HTTP 2xx (success).',
    'denied': 'The response status is any HTTP 4xx (client-side rejection).',
    'same_title': 'The response title equals the created item title.',
    'same_description': 'The response description equals the created item description.',
    'same_id': 'The response item ID equals the created item ID.',
    'same_owner': 'The response owner ID equals the created item owner ID.',
    'updated_title': 'The response title equals the new title supplied in the update.',
    'updated_description': 'The response description equals the new description supplied in the update.',
    'item_not_found': 'The JSON detail has the exact text Item not found.',
    'no_permission': 'The JSON detail has the exact text Not enough permissions.',
    'wrong_password': 'The JSON detail has the exact text Incorrect email or password.',
    'no_token': 'The JSON contains no non-empty access token.',
    'has_token': 'The JSON contains a non-empty access token.',
    'same_email': 'The returned email equals the submitted email.',
    'same_name': 'The returned full name equals the submitted full name.',
    'has_user_id': 'The response includes a user ID.',
    'can_login': 'A follow-up login using the submitted credentials succeeds and returns a token.',
}

SCENARIOS = {
    2: Scenario('retrieve created item', '/api/v1/items/{id}', 'get',
                'Sign in as the test admin, create one item, retrieve it by ID.',
                ('same_description', 'http_404', 'same_owner', 'success', 'same_id',
                 'http_200', 'same_title', 'item_not_found')),
    3: Scenario('retrieve missing item', '/api/v1/items/{id}', 'get',
                'Sign in as the test admin, retrieve a fresh UUID with no item.',
                ('http_400', 'item_not_found', 'success', 'http_404', 'denied', 'no_permission')),
    4: Scenario('retrieve another user item', '/api/v1/items/{id}', 'get',
                'Create two ordinary accounts, use the first to create an item, and read it as the second.',
                ('http_403', 'success', 'no_permission', 'http_200', 'denied', 'http_400', 'item_not_found')),
    6: Scenario('update an owned item', '/api/v1/items/{id}', 'put',
                'Sign in as the test admin, create one item, then submit a new title and description.',
                ('same_id', 'updated_description', 'http_400', 'success', 'same_owner',
                 'no_permission', 'http_200', 'updated_title')),
    13: Scenario('wrong-password login', '/api/v1/login/access-token', 'post',
                 'Sign up an ordinary user, then attempt login with an incorrect password.',
                 ('has_token', 'http_400', 'http_401', 'wrong_password', 'no_token', 'denied', 'http_200')),
    34: Scenario('register a new user', '/api/v1/users/signup', 'post',
                 'Submit a fresh email, password and full name. Observe the signup response and whether the credentials work.',
                 ('success', 'has_user_id', 'same_email', 'http_422', 'can_login',
                  'same_name', 'http_400', 'http_200')),
}

ANCHORS = {
    'success': r'\b200\b|\bsucceeds?\b|successfully|matches the created|works as expected',
    'denied': r'\b(?:400|401|403|404|422)\b|not[- ]found response|access is denied|wrong password.*reject|rejects a wrong password',
    'same_title': r'\btitle\b.*exactly match',
    'same_description': r'\bdescription\b.*exactly match',
    'same_id': r'\bid\b.*exactly match|same id|\bid\b and owner_id fields matching',
    'same_owner': r'owner_id.*exactly match|same id and owner|owner_id fields matching',
    'updated_title': r'updated title and description fields matching',
    'updated_description': r'updated title and description fields matching',
    'item_not_found': r"detail.{0,45}['\"]Item not found['\"]",
    'no_permission': r"detail.{0,45}['\"]Not enough permissions['\"]",
    'wrong_password': r"detail.{0,45}['\"]Incorrect email or password['\"]",
    'no_token': r'rejects a wrong password|response status code is 400 and the detail message is .incorrect email or password',
    'has_token': r'access token.{0,20}(non-empty|not empty)',
    'same_email': r'email.{0,28}equals the generated email',
    'same_name': r'full_name.{0,28}equals the generated full name',
    'has_user_id': r"['\"]id['\"] field is present",
    'can_login': r'can log\s?in with the generated credentials',
}


def rule_agrees(check, text):
    pattern = (rf'\b(?:status(?: code)?(?: is| of)?|HTTP)\s+{check[5:]}\b'
               if check in STATUS else ANCHORS[check])
    return re.search(pattern, text, re.I) is not None
