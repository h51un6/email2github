# -*- encoding: UTF-8 -*-

# Standard imports
from typing import List

# Third party imports
from github.GithubException import RateLimitExceededException

# Application imports
from app.logger                      import console
from app.techniques.abstract_handler import AbstractHandler
from app.services.github_service     import GithubService

class UsersSearch(AbstractHandler):
    async def resolve(self, emails: List) -> List:
        with console.status("Searching email addresses…") as status:
            try:
                for email in emails:
                    await GithubService().search_email(email)

                console.print("{:<40s} {:<10s}".format("Searching email addresses:", "done"))

            except RateLimitExceededException:
                console.print("{:<40s} [red]{:<10s}[/red]".format(
                    "Searching email addresses:",
                    "fail (reason: Github API rate limit)"))

        if need_to_be_resolved := list(filter(lambda email: not email.resolved(), emails)):
            return await super().resolve(need_to_be_resolved)
