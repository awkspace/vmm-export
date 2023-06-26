#!/usr/bin/env python3

import json
import logging

from vmm_export.dsm_errors import dsm_errors

logging.basicConfig()
logger = logging.getLogger("vmm_export")


async def dsm_request(session, url, ignore_error=False, **kwargs):
    async with session.get(url, **kwargs) as raw:
        response = await raw.json(content_type=None)
        if not ignore_error:
            if not response["success"]:
                log_dsm_response(kwargs.get("params"), response)
                raise RuntimeError("Unexpected error from DSM")
    return response


def log_dsm_response(params, response):
    error_code = response.get("error", {}).get("code")
    if error_code:
        error = dsm_errors["Common"].get(error_code)
        if error:
            logger.error(f"Error: {error}")

        api = params.get("api")
        if api:
            if not api.startswith("SYNO.API"):
                api = ".".join(params.get("api", "").split(".")[0:2])
            error = dsm_errors.get(api).get(error_code)
            if error:
                logger.error(f"Error: {error}")

    logger.error(f"Full response from DSM: {json.dumps(response)}")
