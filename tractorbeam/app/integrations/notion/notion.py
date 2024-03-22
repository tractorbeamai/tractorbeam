from typing import Any

import httpx

from ..oauth2_integration import OAuth2Integration


class Notion(OAuth2Integration):
    name = "Notion"
    slug = "notion"
    logo_url = "/static/integration-logos/notion.svg"

    oauth2_api_root = "https://api.notion.com"
    oauth2_authorization_endpoint = "/v1/oauth/authorize"
    oauth2_token_endpoint = "/v1/oauth/token"

    api_root = "https://api.notion.com"
    notion_search_endpoint = "/v1/search"
    notion_block_children_endpoint = "/v1/blocks/{block_id}/children"
    notion_database_endpoint = "/v1/databases/{database_id}/query"

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

    @classmethod
    def get_auth_url(
        cls,
        client_id: str,
        redirect_uri: str,
        extra_query_params=None,
    ) -> str:
        extra_query_params = extra_query_params or {}
        extra_query_params.update({"owner": "user"})

        return super().get_auth_url(
            client_id,
            redirect_uri,
            extra_query_params,
        )

    def _read_block(self, block_id: str, num_tabs: int = 0) -> str:
        # https://github.com/run-llama/llama-hub/blob/01400bf31ed336137e36caed6809e48bad1c3621/llama_hub/notion/base.py
        done = False
        result_lines_arr = []
        cur_block_id = block_id
        while not done:
            block_url = self.api_root + self.notion_block_children_endpoint.format(
                block_id=cur_block_id,
            )
            query_dict: dict[str, Any] = {}

            data = httpx.get(
                block_url,
                headers=self._get_headers(),
                params=query_dict,
            ).json()

            for result in data["results"]:
                result_type = result["type"]
                result_obj = result[result_type]

                cur_result_text_arr = []
                if "rich_text" in result_obj:
                    for rich_text in result_obj["rich_text"]:
                        # skip if doesn't have text object
                        if "text" in rich_text:
                            text = rich_text["text"]["content"]
                            prefix = "\t" * num_tabs
                            cur_result_text_arr.append(prefix + text)

                result_block_id = result["id"]
                has_children = result["has_children"]
                if has_children:
                    children_text = self._read_block(
                        result_block_id,
                        num_tabs=num_tabs + 1,
                    )
                    cur_result_text_arr.append(children_text)

                cur_result_text = "\n".join(cur_result_text_arr)
                result_lines_arr.append(cur_result_text)

            if data["next_cursor"] is None:
                done = True
                break

            cur_block_id = data["next_cursor"]

        return "\n".join(result_lines_arr)

    def read_page(self, page_id: str) -> str:
        return self._read_block(page_id)

    def get_all_documents(self) -> list[str]:
        response = httpx.post(
            self.api_root + "/v1/search",
            headers=self._get_headers(),
        )

        data = response.json()

        documents: list[str] = []

        for obj in data["results"]:
            if obj["object"] == "page":
                try:
                    page_id = obj["id"]
                    page_title = obj["properties"]["title"]["title"][0]["plain_text"]
                    page_contents = self.read_page(page_id)

                    documents.append(f"=== {page_title} === \n\n{page_contents}")
                except:
                    continue

        return documents
