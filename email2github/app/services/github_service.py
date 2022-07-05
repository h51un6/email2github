# -*- encoding: UTF-8 -*-

# Standard imports
from os          import path, makedirs, remove
from dataclasses import dataclass

# Third party imports
import json

from github                 import Github, AuthenticatedUser
from github.GithubException import BadCredentialsException, GithubException
from rich.prompt            import Prompt

# Application imports
from app.entities.email import Email
from app.logger             import console

# Singleton

AUTH_FILE         = "tmp/auth.json"
LOGIN_AUTH_METHOD = "login"
TOKEN_AUTH_METHOD = "token"

@dataclass
class GithubService:
    github: Github            = None
    user  : AuthenticatedUser = None

    def configurated(self):
        return path.isfile(AUTH_FILE)

    def authenticated(self):
        try:
            return bool(self.user) and bool(self.user.login)

        except BadCredentialsException as exception:
            return False

    async def configure(self) -> bool:
        directory = path.dirname(AUTH_FILE)

        if directory and not path.isdir(directory) and makedirs(directory) and not path.isdir(directory):
            makedirs(directory)

        # XXX Login authentication method could be used on self-hosted instances
        #     but this method is no longer an option on github.com
        #     https://github.com/PyGithub/PyGithub/issues/1851
        method = Prompt.ask("Choice your authentication method",
                            # choices=[LOGIN_AUTH_METHOD, TOKEN_AUTH_METHOD],
                            choices=[TOKEN_AUTH_METHOD],
                            default=TOKEN_AUTH_METHOD)

        if LOGIN_AUTH_METHOD == method:
            login    = Prompt.ask("Enter your login")
            password = Prompt.ask("Enter your password", password=True)
            auth     = { "login": login, "password": password }
        else:
            token    = Prompt.ask("Enter your token", password=True)
            auth     = { "token": token }

        auth["method"] = method

        with open(AUTH_FILE, "w") as file:
            file.write(json.dumps(auth))

        return True

    async def authenticate(self) -> bool:
        if not self.configurated():
            return False

        with open(AUTH_FILE) as file:
            self.login_or_token = json.loads(file.read())

        try:
            if LOGIN_AUTH_METHOD == self.login_or_token.get("method"):
                self.github = Github(self.login_or_token.get("login"), self.login_or_token.get("password"))
            else:
                self.github = Github(self.login_or_token.get(self.login_or_token.get("method")))

            self.user = self.github.get_user()

            self.user.login

        except BadCredentialsException as exception:
            console.print("{:<40s} [red]{:<10s}[/red]".format("Signing in to Github:", "fail"))
            console.print("{:<40s} {:<10s}".format("Cleaning the cached authentication file:", "done"))

            remove(AUTH_FILE)

            return False

        except GithubException as exception:
            console.print("[red]{:<40s} {:<10s}[/red]".format("Error:", exception.data.get("message")))

            remove(AUTH_FILE)

            return False

        return True

    async def search_email(self, email: Email):
        if not self.authenticated() and not await self.authenticate():
            exit(1)

        users = self.github.search_users("{} in:email".format(email.address))

        for user in users:
            email.user = user
            return True

        return False

    async def create_repository(self, name, *, private=False):
        if not self.authenticated() and not await self.authenticate():
            exit(1)

        return self.user.create_repo(name, private=private)

    async def get_repo(self, name: str):
        if not self.authenticated() and not await self.authenticate():
            exit(1)

        return self.user.get_repo(name)
        # return self.github.get_repo(name)
