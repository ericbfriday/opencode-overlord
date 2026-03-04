#!/usr/bin/env python3
"""REST-compatibility helper for Jules SDK workflows in non-TypeScript environments."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class JulesSDK:
    def __init__(self, api_key: str, base_url: str, dry_run: bool = False) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.dry_run = dry_run

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        query = ""
        if params:
            clean_params = {k: v for k, v in params.items() if v is not None}
            if clean_params:
                query = "?" + urllib.parse.urlencode(clean_params)

        url = f"{self.base_url}{path}{query}"
        payload_bytes = None
        headers = {"x-goog-api-key": self.api_key}

        if body is not None:
            payload_bytes = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        if self.dry_run:
            return {
                "dry_run": True,
                "method": method,
                "url": url,
                "headers": headers,
                "body": body,
            }

        req = urllib.request.Request(url=url, data=payload_bytes, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req) as response:
                raw = response.read().decode("utf-8")
                if not raw:
                    return {}
                return json.loads(raw)
        except urllib.error.HTTPError as err:
            error_body = err.read().decode("utf-8", errors="replace")
            return {
                "error": {
                    "http_status": err.code,
                    "body": error_body,
                }
            }

    def list_sessions(self, page_size: int | None = None, page_token: str | None = None) -> Any:
        return self._request("GET", "/sessions", params={"pageSize": page_size, "pageToken": page_token})

    def get_session(self, session_id: str) -> Any:
        return self._request("GET", f"/sessions/{session_id}")

    def create_session(
        self,
        prompt: str,
        *,
        title: str | None = None,
        source: str | None = None,
        starting_branch: str | None = None,
        require_plan_approval: bool = False,
        automation_mode: str | None = None,
    ) -> Any:
        body: dict[str, Any] = {
            "prompt": prompt,
            "requirePlanApproval": require_plan_approval,
        }
        if title:
            body["title"] = title
        if automation_mode:
            body["automationMode"] = automation_mode
        if source:
            source_context: dict[str, Any] = {"source": source}
            if starting_branch:
                source_context["githubRepoContext"] = {"startingBranch": starting_branch}
            body["sourceContext"] = source_context
        return self._request("POST", "/sessions", body=body)

    def delete_session(self, session_id: str) -> Any:
        return self._request("DELETE", f"/sessions/{session_id}")

    def send_message(self, session_id: str, prompt: str) -> Any:
        return self._request("POST", f"/sessions/{session_id}:sendMessage", body={"prompt": prompt})

    def approve_plan(self, session_id: str) -> Any:
        return self._request("POST", f"/sessions/{session_id}:approvePlan", body={})

    def list_activities(
        self,
        session_id: str,
        page_size: int | None = None,
        page_token: str | None = None,
        create_time: str | None = None,
    ) -> Any:
        return self._request(
            "GET",
            f"/sessions/{session_id}/activities",
            params={"pageSize": page_size, "pageToken": page_token, "createTime": create_time},
        )

    def get_activity(self, session_id: str, activity_id: str) -> Any:
        return self._request("GET", f"/sessions/{session_id}/activities/{activity_id}")

    def list_sources(
        self,
        page_size: int | None = None,
        page_token: str | None = None,
        filter_expr: str | None = None,
    ) -> Any:
        return self._request(
            "GET",
            "/sources",
            params={"pageSize": page_size, "pageToken": page_token, "filter": filter_expr},
        )

    def get_source(self, source_id: str) -> Any:
        return self._request("GET", f"/sources/{source_id}")


def _add_common_parser_args(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument("--page-size", type=int, default=None)
    subparser.add_argument("--page-token", default=None)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SDK-style Jules REST API client")
    parser.add_argument("--api-key", default=os.getenv("JULES_API_KEY", ""))
    parser.add_argument("--base-url", default=os.getenv("JULES_API_BASE", "https://jules.googleapis.com/v1alpha"))
    parser.add_argument("--dry-run", action="store_true")

    sub = parser.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("list-sessions")
    _add_common_parser_args(sp)

    sp = sub.add_parser("get-session")
    sp.add_argument("--session-id", required=True)

    sp = sub.add_parser("create-session")
    sp.add_argument("--prompt", required=True)
    sp.add_argument("--title", default=None)
    sp.add_argument("--source", default=None, help="Resource name, e.g. sources/github-owner-repo")
    sp.add_argument("--starting-branch", default=None)
    sp.add_argument("--require-plan-approval", action="store_true")
    sp.add_argument("--automation-mode", default=None, help="e.g. AUTO_CREATE_PR")

    sp = sub.add_parser("delete-session")
    sp.add_argument("--session-id", required=True)

    sp = sub.add_parser("send-message")
    sp.add_argument("--session-id", required=True)
    sp.add_argument("--prompt", required=True)

    sp = sub.add_parser("approve-plan")
    sp.add_argument("--session-id", required=True)

    sp = sub.add_parser("list-activities")
    sp.add_argument("--session-id", required=True)
    _add_common_parser_args(sp)
    sp.add_argument("--create-time", default=None)

    sp = sub.add_parser("get-activity")
    sp.add_argument("--session-id", required=True)
    sp.add_argument("--activity-id", required=True)

    sp = sub.add_parser("list-sources")
    _add_common_parser_args(sp)
    sp.add_argument("--filter", default=None)

    sp = sub.add_parser("get-source")
    sp.add_argument("--source-id", required=True)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.api_key and not args.dry_run:
        parser.error("API key required: pass --api-key or set JULES_API_KEY")

    sdk = JulesSDK(api_key=args.api_key, base_url=args.base_url, dry_run=args.dry_run)

    if args.command == "list-sessions":
        result = sdk.list_sessions(page_size=args.page_size, page_token=args.page_token)
    elif args.command == "get-session":
        result = sdk.get_session(args.session_id)
    elif args.command == "create-session":
        result = sdk.create_session(
            prompt=args.prompt,
            title=args.title,
            source=args.source,
            starting_branch=args.starting_branch,
            require_plan_approval=args.require_plan_approval,
            automation_mode=args.automation_mode,
        )
    elif args.command == "delete-session":
        result = sdk.delete_session(args.session_id)
    elif args.command == "send-message":
        result = sdk.send_message(args.session_id, args.prompt)
    elif args.command == "approve-plan":
        result = sdk.approve_plan(args.session_id)
    elif args.command == "list-activities":
        result = sdk.list_activities(
            session_id=args.session_id,
            page_size=args.page_size,
            page_token=args.page_token,
            create_time=args.create_time,
        )
    elif args.command == "get-activity":
        result = sdk.get_activity(args.session_id, args.activity_id)
    elif args.command == "list-sources":
        result = sdk.list_sources(page_size=args.page_size, page_token=args.page_token, filter_expr=args.filter)
    elif args.command == "get-source":
        result = sdk.get_source(args.source_id)
    else:
        parser.error(f"Unhandled command: {args.command}")
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
