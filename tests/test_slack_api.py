import asyncio

from aiohttp.web_exceptions import HTTPException
from asynctest import mock
import pytest

from aslack.slack_api import SlackApi, SlackApiError

DUMMY_TOKEN = 'token'


@pytest.mark.parametrize('status,result,error', [
    (200, {'ok': True}, None),
    (200, {'ok': False, 'error': 'foo'}, SlackApiError),
    (500, {}, HTTPException),
])
@mock.patch('aslack.slack_api.aiohttp')
@pytest.mark.asyncio
async def test_execute_method(aiohttp, status, result, error):
    json_future = asyncio.Future()
    json_future.set_result(result)
    resp_future = asyncio.Future()
    resp_future.set_result(mock.MagicMock(
        status=status,
        message='failed',
        **{'json.return_value': json_future}
    ))
    aiohttp.get.return_value = resp_future
    api = SlackApi(DUMMY_TOKEN)
    method = 'auth.test'
    if error is None:
        assert await api.execute_method(method) == result
    else:
        with pytest.raises(error):
            await api.execute_method(method)
    aiohttp.get.assert_called_once_with(
        'https://slack.com/api/{}'.format(method),
        params={'token': DUMMY_TOKEN},
    )


@pytest.mark.parametrize('args,need_token', [
    [(), True],
    [(DUMMY_TOKEN,), False],
])
@mock.patch('aslack.slack_api.get_api_token')
def test_init(get_api_token, args, need_token):
    get_api_token.return_value = DUMMY_TOKEN
    api = SlackApi(*args)
    assert api.token == DUMMY_TOKEN
    if need_token:
        get_api_token.assert_called_once_with()


@pytest.mark.parametrize('method,exists', [
    ('auth.test', True),
    ('foo.bar', False)
])
def test_create_url(method, exists):
    if exists:
        expected = 'https://slack.com/api/{}'.format(method)
        assert SlackApi._create_url(method) == expected
    else:
        with pytest.raises(SlackApiError):
            SlackApi._create_url(method)
