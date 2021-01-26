#!/usr/local/bin/python
import argparse
import collections
import os
import shutil
import time
import asyncio
import aiohttp
import tqdm
import concurrent
from aiohttp import web
from http import HTTPStatus

SERVER_URL = "http://localhost:8001"

URL_FMT = SERVER_URL + "/flags/{cc}/{cc}.gif"
URL_METADATA_FMT = SERVER_URL + "/flags/{cc}/metadata.json"

DEST_DIR = "downloads/"
if os.path.exists(DEST_DIR):
    shutil.rmtree(DEST_DIR)
    os.mkdir(DEST_DIR)
else:
    os.mkdir(DEST_DIR)


ALL_CC = (
    "AD AM AZ BF BN BW CF CM CV DK EG FJ GD GQ HN IE IS KE KN LA LR LY "
    "MG MN MW NE NP PE PT RS SC SK SR SZ TL TT UG VC YE AE AO BA BG BO "
    "BY CG CN CY DM ER FM GE GR HR IL IT KG KP LB LS MA MH MR MX NG NR "
    "PG PW RU SD SL SS TD TM TV US VE ZA AF AR BB BH BR BZ CH CO CZ DZ "
    "ES FR GH GT HT IN JM KH KR LC LT MC MK MT MY NI NZ PH PY RW SE SM "
    "ST TG TN TW UY VN ZM AG AT BD BI BS CA CI CR DE EC ET GA GM GW HU "
    "IQ JO KI KW LI LU MD ML MU MZ NL OM PK QA SA SG SN SV TH TO TZ UZ "
    "VU ZW AL AU BE BJ BT CD CL CU DJ EE FI GB GN GY ID IR JP KM KZ LK "
    "LV ME MM MV NA NO PA PL RO SB SI SO SY TJ TR UA VA WS".split()
)


Result = collections.namedtuple("Result", "status cc")


class FetchError(Exception):
    def __init__(self, country_code):
        self.country_code = country_code


async def http_get(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                ctype = resp.headers.get("Content-Type", "").lower()
                if "json" in ctype or url.endswith("json"):
                    data = await resp.json(content_type="text/plain")
                else:
                    data = await resp.read()

                return data
            elif resp.status == 404:
                raise web.HTTPNotFound(headers=resp.headers, reason=resp.reason)
            else:
                raise web.HTTPInternalServerError(
                    headers=resp.headers, reason=resp.reason
                )


async def get_country(cc):
    url = URL_METADATA_FMT.format(cc=cc.lower())
    metadata = await http_get(url)
    return metadata["country"]


async def get_flag(cc):
    url = URL_FMT.format(cc=cc.lower())
    return await http_get(url)


def save_flag(img, filename):
    path = os.path.join(DEST_DIR, filename)
    with open(path, "wb") as fp:
        fp.write(img)


async def download_one(cc, semaphore, verbose=False):
    try:
        async with semaphore:
            image = await get_flag(cc)
        async with semaphore:
            country = await get_country(cc)

    except web.HTTPNotFound:
        status = HTTPStatus.NOT_FOUND
        msg = "not found"
    except Exception as exc:
        raise FetchError(cc) from exc
    else:
        country = country.replace(" ", "_")
        filename = f"{country}-{cc}.gif"
        asyncio.get_event_loop().run_in_executor(
            None, save_flag, image, filename
        )
        status = HTTPStatus.OK
        msg = "ok"

    if verbose and msg:
        print(cc, msg)

    return Result(status, cc)


async def downloader_coro(cc_list, verbose, concur_req):
    counter = collections.Counter()
    semaphore = asyncio.Semaphore(concur_req)
    todo = [download_one(cc, semaphore, verbose) for cc in sorted(cc_list)]
    todo_iter = asyncio.as_completed(todo)
    if not verbose:
        todo_iter = tqdm.tqdm(todo_iter, total=len(cc_list))

    for coro in todo_iter:
        try:
            res = await coro
        except FetchError as exc:
            country_code = exc.country_code
            try:
                error_msg = exc.__cause__.args[0]
            except IndexError:
                error_msg = exc.__cause__.__class__.__name__

            if verbose and error_msg:
                msg = "*** Error for {}: {}"
                print(msg.format(country_code, error_msg))

            status = HTTPStatus.INTERNAL_SERVER_ERROR
        else:
            status = res.status

        counter[status] += 1

    return counter


def download_many(cc_list, num_coro=5, verbose=False):
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        loop.set_default_executor(executor)
        coro = downloader_coro(cc_list, verbose, num_coro)
        counts = loop.run_until_complete(coro)

    loop.close()
    return counts


def main(download_many, num_coro=5, verbose=False):
    t0 = time.perf_counter()
    count = download_many(ALL_CC, num_coro, verbose)
    elapsed = time.perf_counter() - t0
    print()
    print(f"donwloaded {count} flags in {elapsed:.4f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verbose", help="print outputs in verbose form", action="store_true"
    )
    parser.add_argument(
        "--net-concur-max",
        help="maximum number of coroutines for networking I/O",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--fs-concur-max",
        help="maximum number of coroutines for filesystem I/O",
        type=int,
        default=3,
    )
    args = parser.parse_args()
    print(args.net_concur_max)
    main(download_many, num_coro=args.net_concur_max, verbose=args.verbose)
