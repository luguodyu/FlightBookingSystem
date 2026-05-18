import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import Mock
from services import UserService


class TestUserService:

    def test_login_success(self):
        mock_user_repo = Mock()
        mock_user_repo.login.return_value = {'user_id': 1, 'username': 'test'}

        service = UserService(mock_user_repo)
        success, user = service.login('test', '123')

        assert success is True
        assert user['username'] == 'test'

    def test_login_empty_username(self):
        mock_user_repo = Mock()
        service = UserService(mock_user_repo)

        success, user = service.login('', '123')
        assert success is False
        assert user is None
        mock_user_repo.login.assert_not_called()

    def test_login_wrong_password(self):
        mock_user_repo = Mock()
        mock_user_repo.login.return_value = None

        service = UserService(mock_user_repo)
        success, user = service.login('test', 'wrong')

        assert success is False
        assert user is None

    def test_register_success(self):
        mock_user_repo = Mock()
        mock_user_repo.register.return_value = True

        service = UserService(mock_user_repo)
        success, msg = service.register('newuser', '123', '123', '张三', '13800138000')

        assert success is True
        assert msg == '注册成功'

    def test_register_password_mismatch(self):
        mock_user_repo = Mock()
        service = UserService(mock_user_repo)

        success, msg = service.register('newuser', '123', '456', '张三', '13800138000')

        assert success is False
        assert '密码不一致' in msg
        mock_user_repo.register.assert_not_called()

    def test_register_empty_username(self):
        mock_user_repo = Mock()
        service = UserService(mock_user_repo)

        success, msg = service.register('', '123', '123', '张三', '13800138000')

        assert success is False
        assert '用户名和密码不能为空' in msg