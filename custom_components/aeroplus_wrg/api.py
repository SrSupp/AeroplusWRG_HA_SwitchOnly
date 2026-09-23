from __future__ import annotations

import asyncio
import json
import logging
import ssl
from typing import Any, Optional

from aiohttp import ClientSession, ClientWebSocketResponse, WSMsgType

_LOGGER = logging.getLogger(__name__)

WS_PATH = "/WebSocket"


class SiegeniaClient:
    """Async WebSocket client for Siegenia Aeroplus WRG devices."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 443,
        use_ssl: bool = True,
        heartbeat_seconds: int = 10,
        session: Optional[ClientSession] = None,
    ) -> None:
        self._host = host
        self._username = username
        self._password = password
        self._port = port
        self._use_ssl = use_ssl
        self._hb = heartbeat_seconds
        self._session = session
        self._ws: Optional[ClientWebSocketResponse] = None
        self._req_id = 0
        self._pending: dict[int, asyncio.Future] = {}
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._receiver_task: Optional[asyncio.Task] = None
        self.on_push = None  # optional callback for unsolicited frames
        self._connect_lock: asyncio.Lock = asyncio.Lock()

    @property
    def connected(self) -> bool:
        return self._ws is not None and not self._ws.closed

    def set_on_push(self, callback) -> None:
        self.on_push = callback

    @staticmethod
    def _iter_json_objects(raw: str):
        decoder = json.JSONDecoder()
        idx = 0
        length = len(raw)
        while True:
            while idx < length and raw[idx].isspace():
                idx += 1
            if idx >= length:
                return
            obj, idx = decoder.raw_decode(raw, idx)
            yield obj

    async def connect(self) -> None:
        async with self._connect_lock:
            if self.connected:
                return

            if self._session is None:
                self._session = ClientSession()

            scheme = "wss" if self._use_ssl else "ws"
            url = f"{scheme}://{self._host}:{self._port}{WS_PATH}"

            ssl_ctx = None
            if self._use_ssl:
                loop = asyncio.get_running_loop()
                ssl_ctx = await loop.run_in_executor(None, ssl.create_default_context)
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE

            _LOGGER.debug("Connecting WS to %s", url)
            self._ws = await self._session.ws_connect(
                url,
                ssl=ssl_ctx,
                headers={"Origin": f"{scheme}://{self._host}:{self._port}"},
            )

            # Start receiver, then log in, then start the heartbeat.
            self._receiver_task = asyncio.create_task(self._receiver())
            await self.login(self._username, self._password)
            self._heartbeat_task = asyncio.create_task(self._heartbeat())
            _LOGGER.debug("WS connected")

    async def _receiver(self) -> None:
        assert self._ws is not None
        ws = self._ws
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    for data in self._iter_json_objects(msg.data):
                        if not isinstance(data, dict):
                            self._dispatch_push(data)
                            continue

                        rid = data.get("id")
                        status = data.get("status")
                        payload = data.get("data")
                        fut = self._pending.pop(rid, None)
                        if fut is not None and not fut.done():
                            fut.set_result((status, payload))
                        else:
                            # unsolicited push
                            self._dispatch_push(data)
                except json.JSONDecodeError as exc:
                    _LOGGER.warning("WS JSON error: %s (%s)", exc, msg.data)
                    continue
            elif msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.ERROR):
                _LOGGER.debug("WS closed: %s", msg.type)
                break

        try:
            if self._ws and not self._ws.closed:
                await self._ws.close()
        except Exception:
            pass
        self._ws = None

    def _dispatch_push(self, data: Any) -> None:
        try:
            if callable(self.on_push):
                self.on_push(data)
        except Exception as exc:
            _LOGGER.debug("on_push callback error: %s", exc)

    async def close(self) -> None:
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
        if self._receiver_task:
            self._receiver_task.cancel()
            self._receiver_task = None
        if self._ws and not self._ws.closed:
            await self._ws.close()
        self._ws = None
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None

    async def _send(self, command: Any, params: Optional[dict] = None, timeout: float = 5.0):
        if not self.connected:
            await self.connect()
            if not self.connected:
                raise RuntimeError("WS not connected")

        self._req_id += 1
        rid = self._req_id

        req: dict[str, Any] = {"command": command} if isinstance(command, str) else dict(command)
        if params is not None:
            req["params"] = params
        req["id"] = rid

        if _LOGGER.isEnabledFor(logging.DEBUG):
            redacted = {k: ("***" if k == "password" else v) for k, v in req.items()}
            _LOGGER.debug("WS SEND: %s", json.dumps(redacted))

        loop = asyncio.get_event_loop()
        fut: asyncio.Future = loop.create_future()
        self._pending[rid] = fut

        try:
            assert self._ws is not None
            await self._ws.send_str(json.dumps(req))
        except Exception:
            # reconnect once and retry
            await self.connect()
            try:
                assert self._ws is not None
                await self._ws.send_str(json.dumps(req))
            except Exception:
                self._pending.pop(rid, None)
                raise

        try:
            status, payload = await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending.pop(rid, None)
            raise TimeoutError("Siegenia request timed out") from None
        _LOGGER.debug("WS RECV for id=%s: status=%s payload=%s", rid, status, payload)
        if status != "ok":
            raise RuntimeError(f"Siegenia error: {status}")
        return payload

    async def login(self, username: str, password: str) -> dict:
        return await self._send(
            {"command": "login", "user": username, "password": password, "long_life": False}
        )

    async def keep_alive(self) -> None:
        await self._send("keepAlive", {"extend_session": True})

    async def _heartbeat(self) -> None:
        while True:
            try:
                await asyncio.sleep(self._hb)
                await self.keep_alive()
            except asyncio.CancelledError:
                return
            except Exception as exc:
                _LOGGER.debug("Heartbeat error: %s", exc)

    # Device commands actually used by this integration.
    async def get_device(self) -> dict:
        return await self._send("getDevice")

    async def get_device_state(self) -> dict:
        return await self._send("getDeviceState")

    async def get_device_params(self) -> dict:
        return await self._send("getDeviceParams")

    async def set_device_active(self, active: bool) -> dict:
        # getDeviceState reports the on/off flag flat as "deviceactive", but
        # setDeviceParams expects it nested below "devicestate". Sent flat,
        # the device silently accepts the call and ignores it.
        return await self._send("setDeviceParams", params={"devicestate": {"deviceactive": active}})

    async def set_device_params(self, params: dict) -> dict:
        # Unlike deviceactive, fanmode/fanpower/automode_maxairflow are
        # top-level getDeviceParams fields (confirmed via
        # Apollon77/ioBroker.siegenia's device-type-14/AEROPLUS field map) and
        # are written flat, e.g. {"fanmode": "AUTO"}.
        return await self._send("setDeviceParams", params=params)
