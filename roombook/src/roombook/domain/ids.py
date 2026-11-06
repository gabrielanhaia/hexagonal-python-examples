"""Identifiers: plain strings that mypy keeps apart."""

from typing import NewType

RoomId = NewType("RoomId", str)
MemberId = NewType("MemberId", str)
BookingId = NewType("BookingId", str)
